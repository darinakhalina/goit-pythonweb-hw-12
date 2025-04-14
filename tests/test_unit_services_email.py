import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi_mail.errors import ConnectionErrors
from src.services.email import send_email, send_reset_email


@pytest.mark.asyncio
async def test_send_email_success(monkeypatch):
    mock_send_message = AsyncMock()
    monkeypatch.setattr("src.services.email.FastMail.send_message", mock_send_message)
    await send_email(
        email="email@example.com", username="doon", host="https://example.com"
    )

    mock_send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_reset_email(monkeypatch):
    mock_send_message = AsyncMock()
    monkeypatch.setattr("src.services.email.FastMail.send_message", mock_send_message)
    await send_reset_email(
        email="email@example.com", token="token", host="https:/example.com"
    )

    mock_send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_email_connection_error(monkeypatch, capsys):
    async def raise_error(*args, **kwargs):
        raise ConnectionErrors("Simulated connection error")

    monkeypatch.setattr("src.services.email.FastMail.send_message", raise_error)
    await send_email(
        email="email@example.com", username="doon", host="https://example.com"
    )

    captured = capsys.readouterr()
    assert "Simulated connection error" in captured.out


@pytest.mark.asyncio
async def test_send_reset_email_success(monkeypatch):
    mock_send_message = AsyncMock()
    monkeypatch.setattr("src.services.email.FastMail.send_message", mock_send_message)
    await send_reset_email(
        email="email@example.com", token="sometoken", host="https://example.com"
    )

    mock_send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_reset_email_connection_error(monkeypatch, capsys):
    async def raise_error(*args, **kwargs):
        raise ConnectionErrors("Simulated connection error")

    monkeypatch.setattr("src.services.email.FastMail.send_message", raise_error)
    await send_reset_email(
        email="email@example.com", token="token", host="https://example.com"
    )

    captured = capsys.readouterr()
    assert "Simulated connection error" in captured.out


@pytest.mark.asyncio
async def test_send_reset_email_token_generated(monkeypatch):
    mock_send_message = AsyncMock()
    mock_create_token = MagicMock(return_value="generated-token")
    monkeypatch.setattr("src.services.email.FastMail.send_message", mock_send_message)
    monkeypatch.setattr("src.services.email.create_token", mock_create_token)
    await send_reset_email(
        email="email@example.com", token="ignored-token", host="https://example.com"
    )

    mock_create_token.assert_called_once_with(payload={"sub": "email@example.com"})
    mock_send_message.assert_awaited_once()
