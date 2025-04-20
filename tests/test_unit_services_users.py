import pytest
from unittest.mock import AsyncMock, patch
from src.services.users import UserService
from src.schemas.users import UserCreate, UserUpdate
from src.database.models import User
from src.exceptions.exceptions import HTTPNotFoundException


@pytest.fixture
def mock_repo(monkeypatch):
    repo_mock = AsyncMock()
    monkeypatch.setattr("src.services.users.UserRepository", lambda db: repo_mock)
    return repo_mock


@pytest.fixture
def user_data():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        avatar="avatar_url",
        confirmed=True,
        password="hashed_pwd",
    )


@pytest.mark.asyncio
async def test_create_user(mock_repo):
    mock_repo.create_user.return_value = {"email": "test@example.com"}
    user_create = UserCreate(
        username="testuser", email="test@example.com", password="123456", role="user"
    )
    service = UserService(db=AsyncMock())
    with patch("src.services.users.Gravatar.get_image", return_value="avatar_url"):
        result = await service.create_user(user_create)

    assert result["email"] == "test@example.com"
    mock_repo.create_user.assert_awaited_once_with(user_create, "avatar_url")


@pytest.mark.asyncio
async def test_get_user_by_id_found(mock_repo, user_data):
    mock_repo.get_user_by_id.return_value = user_data
    service = UserService(db=AsyncMock())
    result = await service.get_user_by_id(1)

    assert result == user_data
    mock_repo.get_user_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(mock_repo):
    mock_repo.get_user_by_id.return_value = None
    service = UserService(db=AsyncMock())

    with pytest.raises(HTTPNotFoundException):
        await service.get_user_by_id(999)


@pytest.mark.asyncio
async def test_get_user_by_username(mock_repo, user_data):
    mock_repo.get_user_by_username.return_value = user_data
    service = UserService(db=AsyncMock())
    result = await service.get_user_by_username("testuser")

    assert result == user_data
    mock_repo.get_user_by_username.assert_awaited_once_with("testuser")


@pytest.mark.asyncio
async def test_get_user_by_email(mock_repo, user_data):
    mock_repo.get_user_by_email.return_value = user_data
    service = UserService(db=AsyncMock())
    result = await service.get_user_by_email("test@example.com")

    assert result == user_data
    mock_repo.get_user_by_email.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_update_avatar_url_found(mock_repo, user_data):
    mock_repo.get_user_by_email.return_value = user_data
    mock_repo.update_avatar_url.return_value = {
        "email": "test@example.com",
        "avatar": "new_url",
    }
    service = UserService(db=AsyncMock())
    result = await service.update_avatar_url("test@example.com", "new_url")

    assert result["avatar"] == "new_url"
    mock_repo.update_avatar_url.assert_awaited_once_with("test@example.com", "new_url")


@pytest.mark.asyncio
async def test_update_avatar_url_not_found(mock_repo):
    mock_repo.get_user_by_email.return_value = None
    service = UserService(db=AsyncMock())

    with pytest.raises(HTTPNotFoundException):
        await service.update_avatar_url("notfound@example.com", "url")


@pytest.mark.asyncio
async def test_verify_email(mock_repo):
    service = UserService(db=AsyncMock())
    await service.verify_email("test@example.com")
    mock_repo.verify_email.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_update_user(mock_repo, user_data):
    body = UserUpdate(username="updated")
    mock_repo.update_user.return_value = {"username": "updated"}
    service = UserService(db=AsyncMock())
    result = await service.update_user(user_data, body)

    assert result["username"] == "updated"
    mock_repo.update_user.assert_awaited_once_with(user_data, body)


@pytest.mark.asyncio
async def test_create_user_without_avatar(mock_repo):
    user_create = UserCreate(
        username="testuser", email="test@example.com", password="123456", role="user"
    )
    mock_repo.create_user.return_value = {"email": "test@example.com", "avatar": None}
    with patch(
        "libgravatar.Gravatar.get_image", side_effect=Exception("Gravatar error")
    ):
        service = UserService(db=AsyncMock())
        result = await service.create_user(user_create)

        assert result["email"] == "test@example.com"
        assert result.get("avatar") is None
