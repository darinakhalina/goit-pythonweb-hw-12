from unittest.mock import Mock, patch, MagicMock, AsyncMock
import pytest
from sqlalchemy import select
import pytest_asyncio

from src.database.models import User
from conftest import TestingSessionLocal, test_user
from src.services.auth import create_access_token


@pytest_asyncio.fixture
async def get_token():
    token = await create_access_token(payload={"sub": "test_email@example.com"})
    return token


@pytest.fixture
def mock_dependencies(monkeypatch):
    mock_user_service_instance = AsyncMock()
    mock_user_service_class = MagicMock(return_value=mock_user_service_instance)
    monkeypatch.setattr("src.api.auth.UserService", mock_user_service_class)
    mock_logger = MagicMock()
    monkeypatch.setattr("src.api.auth.logger", mock_logger)
    mock_update = AsyncMock()
    monkeypatch.setattr("src.api.auth.update_cached_current_user", mock_update)

    mock_user_service_instance.get_user_by_email.return_value = MagicMock(
        email="test_email@example.com", confirmed=False
    )

    return mock_user_service_instance, mock_logger, mock_update


user_data = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
    "role": "admin",
}


@pytest.fixture
def mock_send_email(monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    return mock_send_email


def test_register_user_creates_account_successfully(client, mock_send_email):
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data


def test_login_fails_for_unconfirmed_user(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    data = response.json()

    assert response.status_code == 401, response.text
    assert data["detail"] == "User is not confirmed."


@pytest.mark.asyncio
async def test_login_user_when_confirmed(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if not current_user:
            pytest.fail(f"User with email {user_data.get('email')} not found")

        setattr(current_user, "confirmed", True)
        await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    data = response.json()

    assert response.status_code == 200, response.text
    assert "access_token" in data
    assert "token_type" in data
    assert isinstance(data["access_token"], str)


def test_login_user_wrong_password(client):
    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("username"), "password": "wrongpassword"},
    )
    data = response.json()

    assert response.status_code == 401, response.text
    assert data["detail"] == "Incorrect login or/and password."


def test_login_user_wrong_username(client):
    response = client.post(
        "api/auth/login",
        data={"username": "wrongusername", "password": user_data.get("password")},
    )
    data = response.json()

    assert response.status_code == 401, response.text
    assert data["detail"] == "Incorrect login or/and password."


def test_login_user_missing_username(client):
    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )
    data = response.json()

    assert response.status_code == 400, response.text
    assert "detail" in data


@pytest.mark.asyncio
async def test_verify_email(client, get_reset_token):
    token = get_reset_token

    response = client.get(f"api/auth/verify_email/{token}")
    data = response.json()

    assert response.status_code == 200, response.text
    assert "message" in data

    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == test_user.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        assert current_user.confirmed is True


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    invalid_token = "invalid_token"

    response = client.get(f"api/auth/verify_email/{invalid_token}")
    data = response.json()

    assert response.status_code == 400, response.text
    assert data["detail"] == "Invalid or expired token"


def test_password_reset_with_nonexistent_email(client):
    non_existent_email = "nonexistent@example.com"
    response = client.post(
        "api/auth/password-reset/", json={"email": non_existent_email}
    )
    data = response.json()

    assert response.status_code == 401, response.text
    assert data["detail"] == "Unauthorized"


def test_login_missing_username(client):
    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )
    data = response.json()

    assert response.status_code == 400, response.text
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) == 1
    assert data["detail"][0]["msg"] == "Field required"
    assert data["detail"][0]["loc"] == ["body", "username"]


def test_login_missing_password(client):
    response = client.post(
        "api/auth/login", data={"username": user_data.get("username")}
    )
    data = response.json()

    assert response.status_code == 400, response.text
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) == 1
    assert data["detail"][0]["msg"] == "Field required"
    assert data["detail"][0]["loc"] == ["body", "password"]


def test_register_user_with_existing_username(client):
    user_with_existing_username = user_data.copy()
    user_with_existing_username["email"] = "anotheremail@example.com"

    with patch(
        "src.services.users.UserService.get_user_by_email", return_value=None
    ), patch(
        "src.services.users.UserService.get_user_by_username"
    ) as mock_username_check:

        mock_username_check.return_value = User(
            id=99,
            username=user_with_existing_username["username"],
            email="other@example.com",
            avatar="avatar_url",
            role="user",
            confirmed=True,
        )

        response = client.post("api/auth/register", json=user_with_existing_username)
        data = response.json()

        assert response.status_code == 409, response.text
        assert data["detail"] == "Cannot create user, username already exists."


def test_register_user_with_existing_email(client):
    user_with_existing_email = user_data.copy()
    user_with_existing_email["username"] = "new_unique_username"

    with patch(
        "src.services.users.UserService.get_user_by_email"
    ) as mock_get_email, patch(
        "src.services.users.UserService.get_user_by_username", return_value=None
    ):

        mock_get_email.return_value = User(
            id=42,
            username="someuser",
            email=user_with_existing_email["email"],
            avatar="someavatar",
            role="user",
            confirmed=True,
        )

        response = client.post("api/auth/register", json=user_with_existing_email)
        data = response.json()

        assert response.status_code == 409, response.text
        assert data["detail"] == "Cannot create user, email already in use."


def test_register_user_success(client, mock_send_email):
    new_user_data = user_data.copy()
    new_user_data["username"] = "uniqueuser"
    new_user_data["email"] = "unique@example.com"
    new_user_data["avatar"] = "some.png"

    with patch(
        "src.services.users.UserService.get_user_by_email", return_value=None
    ), patch(
        "src.services.users.UserService.get_user_by_username", return_value=None
    ), patch(
        "src.services.users.UserService.create_user"
    ) as mock_create_user:

        mock_create_user.return_value = User(
            id=1,
            username=new_user_data["username"],
            email=new_user_data["email"],
            avatar=new_user_data["avatar"],
            role=new_user_data["role"],
            confirmed=False,
        )

        response = client.post("api/auth/register", json=new_user_data)
        data = response.json()

        assert response.status_code == 201, response.text
        assert data["username"] == new_user_data["username"]
        assert data["email"] == new_user_data["email"]
        assert "avatar" in data

        mock_create_user.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_with_existing_email(client):
    user_with_existing_email = user_data.copy()
    user_with_existing_email["username"] = "new_unique_username"

    with patch(
        "src.services.users.UserService.get_user_by_email"
    ) as mock_get_email, patch(
        "src.services.users.UserService.get_user_by_username", return_value=None
    ):

        mock_get_email.return_value = User(
            id=42,
            username="someuser",
            email=user_with_existing_email["email"],
            avatar="someavatar",
            role="user",
            confirmed=True,
        )

        response = client.post("api/auth/register", json=user_with_existing_email)
        data = response.json()

        assert response.status_code == 409, response.text
        assert data["detail"] == "Cannot create user, email already in use."


def test_register_user_success_with_logging(client, mock_send_email):
    new_user_data = user_data.copy()
    new_user_data["username"] = "uniqueuser"
    new_user_data["email"] = "unique@example.com"

    with patch(
        "src.services.users.UserService.get_user_by_email", return_value=None
    ), patch(
        "src.services.users.UserService.get_user_by_username", return_value=None
    ), patch(
        "src.services.users.UserService.create_user"
    ) as mock_create_user, patch(
        "src.api.auth.logger"
    ) as mock_logger:

        mock_create_user.return_value = User(
            id=1,
            username=new_user_data["username"],
            email=new_user_data["email"],
            avatar="some.png",
            role=new_user_data["role"],
            confirmed=False,
        )

        response = client.post("api/auth/register", json=new_user_data)
        data = response.json()

        assert response.status_code == 201, response.text
        assert data["username"] == new_user_data["username"]
        assert data["email"] == new_user_data["email"]
        assert "avatar" in data

        mock_logger.info.assert_called_once_with(
            f'Email sent for "{new_user_data["username"]}".'
        )


def test_login_fails_for_incorrect_credentials(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": "wrongpassword",
        },
    )
    data = response.json()

    assert response.status_code == 401, response.text
    assert data["detail"] == "Incorrect login or/and password."


@pytest.mark.asyncio
async def test_login_fails_for_nonexistent_user(client):
    async with TestingSessionLocal() as session:
        non_existent_user = await session.execute(
            select(User).where(User.username == "nonexistentuser")
        )
        non_existent_user = non_existent_user.scalar_one_or_none()

        if non_existent_user:
            pytest.fail(f"Unexpectedly found user with username nonexistentuser")

    response = client.post(
        "api/auth/login",
        data={
            "username": "nonexistentuser",
            "password": "any_password",
        },
    )
    data = response.json()
    assert response.status_code == 401, response.text
    assert data["detail"] == "Incorrect login or/and password."


@pytest.mark.asyncio
async def test_login_user(client, get_token):
    with patch(
        "src.services.users.UserService.get_user_by_username"
    ) as mock_get_user_by_username, patch(
        "src.services.auth.Hash.verify_password"
    ) as mock_verify_password:
        mock_user = User(
            id=1,
            username="deadpool",
            email="deadpool@example.com",
            password="hashedpassword",
            role="admin",
            confirmed=True,
        )
        mock_get_user_by_username.return_value = mock_user

        mock_verify_password.return_value = True
        response = client.post(
            "api/auth/login", data={"username": "deadpool", "password": "12345678"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_invalid_credentials(client):
    with patch(
        "src.services.users.UserService.get_user_by_username"
    ) as mock_get_user_by_username, patch(
        "src.services.auth.Hash.verify_password"
    ) as mock_verify_password:

        mock_get_user_by_username.return_value = None
        response = client.post(
            "api/auth/login", data={"username": "deadpool", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect login or/and password."}


@pytest.mark.asyncio
async def test_login_user_unconfirmed(client):
    with patch(
        "src.services.users.UserService.get_user_by_username"
    ) as mock_get_user_by_username, patch(
        "src.services.auth.Hash.verify_password"
    ) as mock_verify_password:

        mock_get_user_by_username.return_value = MagicMock(
            username="deadpool", password="hashedpassword", confirmed=False
        )
        mock_verify_password.return_value = True
        response = client.post(
            "api/auth/login", data={"username": "deadpool", "password": "12345678"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "User is not confirmed."}


@pytest.mark.asyncio
async def test_login_user_incorrect_password(client):
    with patch(
        "src.services.users.UserService.get_user_by_username"
    ) as mock_get_user_by_username, patch(
        "src.services.auth.Hash.verify_password"
    ) as mock_verify_password:
        mock_get_user_by_username.return_value = MagicMock(
            username="deadpool", password="hashedpassword", confirmed=True
        )

        mock_verify_password.return_value = False
        response = client.post(
            "api/auth/login", data={"username": "deadpool", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect login or/and password."}


@pytest.mark.asyncio
async def test_verify_email(client, get_token, mock_dependencies):
    mock_user_service, mock_logger, mock_update_cached_current_user = mock_dependencies
    token = get_token
    response = client.get(f"api/auth/verify_email/{token}")

    assert response.status_code == 200
    assert response.json()["message"] == "Email has been successfully confirmed."
    mock_user_service.verify_email.assert_called_once_with("test_email@example.com")
    mock_logger.info.assert_called_once_with(
        "Email address test_email@example.com verified."
    )


@pytest.mark.asyncio
async def test_verify_email_user_not_found(client, get_token, mock_dependencies):
    mock_user_service, mock_logger, mock_update_cached_current_user = mock_dependencies
    token = get_token

    mock_user_service.get_user_by_email = AsyncMock(return_value=None)

    response = client.get(f"api/auth/verify_email/{token}")
    print(response)

    assert response.status_code == 400
    assert response.json() == {"detail": "Verification error"}
    mock_user_service.verify_email.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_update_cached_current_user.assert_not_called()


@pytest.mark.asyncio
async def test_verify_email_already_confirmed(client, get_token, mock_dependencies):
    mock_user_service, mock_logger, mock_update_cached_current_user = mock_dependencies
    token = get_token

    mock_user = AsyncMock()
    mock_user.confirmed = True
    mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

    response = client.get(f"api/auth/verify_email/{token}")

    assert response.status_code == 200
    assert response.json() == {"message": "Email is already confirmed."}

    mock_user_service.verify_email.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_update_cached_current_user.assert_not_called()


@pytest.mark.asyncio
async def test_password_reset_user_not_found(client, mock_dependencies):
    mock_user_service, mock_logger, mock_update_cached_current_user = mock_dependencies
    request_data = {"email": "non_existent_email@example.com"}
    mock_user_service.get_user_by_email = AsyncMock(return_value=None)

    response = client.post("api/auth/password-reset/", json=request_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

    mock_user_service.reset_password.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_update_cached_current_user.assert_not_called()


@pytest.mark.asyncio
async def test_password_reset_success(client, mock_dependencies):
    mock_user_service, mock_logger, mock_update_cached_current_user = mock_dependencies

    mock_user = AsyncMock()
    mock_user.email = "test@example.com"
    mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

    with patch(
        "src.api.auth.create_token", return_value="test_token"
    ) as mock_create_token, patch("src.api.auth.send_reset_email") as mock_send_email:

        response = client.post(
            "/api/auth/password-reset/", json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Reset password email sent"
        mock_create_token.assert_called_once_with(payload={"sub": "test@example.com"})
        mock_send_email.assert_called_once_with(
            "test@example.com", "test_token", "http://testserver/"
        )
        mock_logger.info.assert_called_once_with(
            'Reset password email sent for a user with email address "test@example.com".'
        )
        mock_update_cached_current_user.assert_called_once_with(mock_user)


@pytest.mark.asyncio
@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
@patch("src.api.auth.UserService")
async def test_password_reset_confirm_success(
    mock_user_service_cls, mock_get_email_from_token, client
):
    test_email = "test@example.com"
    test_password = "newpassword123"
    test_token = "somevalidtoken"

    mock_get_email_from_token.return_value = test_email

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = User(email=test_email)
    mock_user_service.update_user.return_value = True
    mock_user_service_cls.return_value = mock_user_service

    payload = {"token": test_token, "password": test_password}

    response = client.post("api/auth/password-reset-confirm/", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Password updated"}
    mock_get_email_from_token.assert_awaited_once_with(test_token)
    mock_user_service.get_user_by_email.assert_awaited_once_with(test_email)
    mock_user_service.update_user.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
@patch("src.api.auth.UserService")
async def test_password_reset_confirm_invalid_token(
    mock_user_service_cls, mock_get_email_from_token, client
):
    test_token = "invalidtoken"
    test_password = "anypassword"

    mock_get_email_from_token.return_value = "notfound@example.com"

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = None
    mock_user_service_cls.return_value = mock_user_service

    payload = {"token": test_token, "password": test_password}

    response = client.post("api/auth/password-reset-confirm/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"
