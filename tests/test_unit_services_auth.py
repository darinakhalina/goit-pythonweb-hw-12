import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from src.services.auth import (
    create_access_token,
    get_current_user,
    get_current_user_admin,
    get_email_from_token,
)
from src.conf.config import settings
from src.database.models import User, UserRole
from src.exceptions.exceptions import HTTPUnauthorizedException, HTTPBadRequestException


@pytest.mark.asyncio
async def test_create_access_token_default_expiration():
    payload = {"sub": "testuser"}
    token = await create_access_token(payload)
    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded


@pytest.mark.asyncio
async def test_get_current_user_from_cache(monkeypatch):
    mock_user = User(id=1, username="testuser", role=UserRole.USER)
    monkeypatch.setattr(
        "src.services.auth.get_cached_current_user", AsyncMock(return_value=mock_user)
    )
    monkeypatch.setattr(
        "src.services.auth.jwt.decode", MagicMock(return_value={"sub": "testuser"})
    )
    result = await get_current_user(token="sometoken", db=AsyncMock())
    assert result == mock_user


@pytest.mark.asyncio
async def test_get_current_user_from_db(monkeypatch):
    mock_user = User(id=2, username="dbuser", role=UserRole.USER)
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_username.return_value = mock_user
    monkeypatch.setattr(
        "src.services.auth.get_cached_current_user", AsyncMock(return_value=None)
    )
    monkeypatch.setattr("src.services.auth.update_cached_current_user", AsyncMock())
    monkeypatch.setattr(
        "src.services.auth.jwt.decode", MagicMock(return_value={"sub": "dbuser"})
    )
    monkeypatch.setattr(
        "src.services.auth.UserService", MagicMock(return_value=mock_user_service)
    )
    result = await get_current_user(token="token", db=AsyncMock())
    assert result.username == "dbuser"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    monkeypatch.setattr(
        "src.services.auth.jwt.decode", MagicMock(side_effect=JWTError("bad token"))
    )
    with pytest.raises(HTTPUnauthorizedException):
        await get_current_user(token="badtoken", db=AsyncMock())


def test_get_current_user_admin_success():
    user = User(id=1, username="admin", role=UserRole.ADMIN)
    result = get_current_user_admin(current_user=user)
    assert result == user


def test_get_current_user_admin_forbidden():
    user = User(id=2, username="user", role=UserRole.USER)
    with pytest.raises(HTTPException) as exc:
        get_current_user_admin(current_user=user)
    assert exc.value.status_code == 403
    assert exc.value.detail == "Permission Denided"


@pytest.mark.asyncio
async def test_get_email_from_token_success(monkeypatch):
    monkeypatch.setattr(
        "src.services.auth.jwt.decode",
        MagicMock(return_value={"sub": "user@example.com"}),
    )
    email = await get_email_from_token("token")
    assert email == "user@example.com"


@pytest.mark.asyncio
async def test_get_email_from_token_invalid(monkeypatch):
    monkeypatch.setattr(
        "src.services.auth.jwt.decode", MagicMock(side_effect=JWTError("invalid"))
    )
    with pytest.raises(HTTPBadRequestException):
        await get_email_from_token("badtoken")


@pytest.mark.asyncio
async def test_create_access_token_with_custom_expiration():
    payload = {"sub": "customuser"}
    expires_in = 60
    token = await create_access_token(payload, expires_delta=expires_in)
    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert decoded["sub"] == "customuser"
    assert "exp" in decoded
    expected_exp = datetime.now(UTC) + timedelta(seconds=expires_in)
    actual_exp = datetime.fromtimestamp(decoded["exp"], tz=UTC)
    delta = abs((actual_exp - expected_exp).total_seconds())
    assert delta < 5


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    def mock_jwt_decode(token, secret, algorithms):
        raise JWTError("Invalid token format")

    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt_decode)
    monkeypatch.setattr("src.services.auth.get_cached_current_user", AsyncMock())
    with pytest.raises(HTTPUnauthorizedException) as exc:
        await get_current_user(token="fake.token.here", db=AsyncMock())
    assert "Could not validate credentials" in str(exc.value)


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(monkeypatch):
    monkeypatch.setattr(
        "src.services.auth.jwt.decode", MagicMock(return_value={"sub": "testuser"})
    )
    monkeypatch.setattr(
        "src.services.auth.get_cached_current_user", AsyncMock(return_value=None)
    )
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_username = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.auth.UserService", MagicMock(return_value=mock_user_service)
    )
    monkeypatch.setattr("src.services.auth.update_cached_current_user", AsyncMock())
    with pytest.raises(HTTPUnauthorizedException) as exc:
        await get_current_user(token="valid.token.here", db=AsyncMock())

    assert "Could not validate credentials" in str(exc.value)


@pytest.mark.asyncio
async def test_get_current_user_username_is_none(monkeypatch):
    monkeypatch.setattr(
        "src.services.auth.jwt.decode", MagicMock(return_value={"sub": None})
    )
    monkeypatch.setattr("src.services.auth.get_cached_current_user", AsyncMock())
    monkeypatch.setattr("src.services.auth.UserService", MagicMock())
    monkeypatch.setattr("src.services.auth.update_cached_current_user", AsyncMock())
    with pytest.raises(HTTPUnauthorizedException) as exc:
        await get_current_user(token="valid.token.without.username", db=AsyncMock())

    assert "Could not validate credentials" in str(exc.value)
