import pytest
import json
from unittest.mock import AsyncMock
from src.database.models import User
from src.services.cache import update_cached_current_user, get_cached_current_user


@pytest.fixture
def mock_redis():
    mock_redis = AsyncMock()
    return mock_redis


@pytest.fixture
def user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        role="user",
        avatar="http://avatar.url",
        confirmed=True,
    )


@pytest.mark.asyncio
async def test_update_cached_current_user(mock_redis, user, monkeypatch):
    monkeypatch.setattr("src.services.cache.redis_client", mock_redis)
    await update_cached_current_user(user)
    expected_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "avatar": user.avatar,
        "confirmed": user.confirmed,
    }
    mock_redis.set.assert_awaited_once_with(
        f"user:{user.username}", json.dumps(expected_data), ex=60
    )


@pytest.mark.asyncio
async def test_get_cached_current_user_success(mock_redis, user, monkeypatch):
    monkeypatch.setattr("src.services.cache.redis_client", mock_redis)
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "avatar": user.avatar,
        "confirmed": user.confirmed,
    }
    mock_redis.get.return_value = json.dumps(user_data)
    result = await get_cached_current_user(username=user.username)

    assert result is not None
    assert isinstance(result, User)
    assert result.id == user.id
    assert result.username == user.username
    assert result.email == user.email
    assert result.role == user.role
    assert result.avatar == user.avatar
    assert result.confirmed == user.confirmed
    mock_redis.get.assert_awaited_once_with(f"user:{user.username}")


@pytest.mark.asyncio
async def test_get_cached_current_user_not_found(mock_redis, monkeypatch):
    monkeypatch.setattr("src.services.cache.redis_client", mock_redis)
    mock_redis.get.return_value = None
    result = await get_cached_current_user(username="nonexistent")

    assert result is None
    mock_redis.get.assert_awaited_once_with("user:nonexistent")


@pytest.mark.asyncio
async def test_get_cached_current_user_invalid_json(mock_redis, monkeypatch, capsys):
    monkeypatch.setattr("src.services.cache.redis_client", mock_redis)
    mock_redis.get.return_value = "invalid_json_data"
    result = await get_cached_current_user(username="testuser")

    assert result is None
    mock_redis.get.assert_awaited_once_with("user:testuser")
    captured = capsys.readouterr()
    assert "Failed to decode user data from cache" in captured.out
