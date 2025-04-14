import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User, UserRole
from src.repository.users import UserRepository
from src.schemas.users import UserCreate, UserUpdate


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user():
    return User(id=1, username="Mock", email="testuser@example.com", role="admin")


@pytest.fixture
def admin_user():
    return User(id=1, username="Mock", email="testuser@example.com", role="user")


@pytest.fixture
def repository(mock_session):
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_get_user_by_email(repository, mock_session, user):
    email = "test@example.com"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(
        id=1,
        username="test",
        email=email,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)
    user = await repository.get_user_by_email(email=email)

    assert user is not None
    assert user.id == 1
    assert user.email == email


@pytest.mark.asyncio
async def test_get_user_by_id(repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(
        id=1,
        username="test",
        email="test@example.com",
    )
    mock_session.execute = AsyncMock(return_value=mock_result)
    user = await repository.get_user_by_id(user_id=1)

    assert user is not None
    assert user.id == 1
    assert user.username == "test"


@pytest.mark.asyncio
async def test_get_user_by_username(repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(
        id=1,
        username="test",
        email="test@example.com",
    )
    mock_session.execute = AsyncMock(return_value=mock_result)
    user = await repository.get_user_by_username(username="test")

    assert user is not None
    assert user.id == 1
    assert user.username == "test"


@pytest.mark.asyncio
async def test_create(repository, mock_session):
    user_data = UserCreate(
        username="test",
        password="111",
        email="test@example.com",
        role=UserRole.USER,
    )
    result = await repository.create_user(body=user_data, avatar="avatar.url")

    assert isinstance(result, User)
    assert result.username == "test"
    assert result.avatar == "avatar.url"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update(repository, mock_session):
    user_data = UserUpdate(password="111222")
    existing_user = User(
        username="test",
        password="1111",
        email="test@example.com",
        role=UserRole.USER,
    )
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    result = await repository.update_user(user=existing_user, body=user_data)
    assert result is True
    assert existing_user.password == "111222"
    assert existing_user.username == "test"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_user)


@pytest.mark.asyncio
async def test_update_avatar(repository, mock_session):
    email = "test@example.com"
    avatar = "avatar.url"
    existing_user = User(username="test", email=email, avatar=None)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    result = await repository.update_avatar_url(email=email, url=avatar)

    assert result is not None
    assert result.username == "test"
    assert result.avatar == avatar
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_user)


@pytest.mark.asyncio
async def test_verify_email(repository, mock_session):
    email = "test@example.com"
    existing_user = User(
        username="test",
        email=email,
        confirmed=False,
        role=UserRole.USER,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    await repository.verify_email(email=email)

    assert existing_user.confirmed is True
    mock_session.commit.assert_awaited_once()
