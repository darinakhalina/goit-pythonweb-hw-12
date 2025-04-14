import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import UploadFile
from io import BytesIO
from src.services.upload import UploadService, CloudinaryUploadService


@pytest.mark.asyncio
async def test_send_email(monkeypatch):
    mock_upload_file = AsyncMock()
    monkeypatch.setattr(
        "src.services.upload.CloudinaryUploadService.upload_file", mock_upload_file
    )
    upload_service = UploadService(CloudinaryUploadService())
    await upload_service.upload_file(file="file", username="username")

    mock_upload_file.assert_called_once_with("file", "username")


def test_cloudinary_config(monkeypatch):
    mock_config = lambda **kwargs: kwargs
    monkeypatch.setattr("src.services.upload.cloudinary.config", mock_config)

    service = CloudinaryUploadService()

    assert isinstance(service, CloudinaryUploadService)


def test_cloudinary_upload_file(monkeypatch):
    mock_upload_response = {"version": "123456"}

    # Mock cloudinary methods
    monkeypatch.setattr(
        "src.services.upload.cloudinary.uploader.upload",
        lambda file, public_id, overwrite: mock_upload_response,
    )

    mock_build_url = MagicMock(return_value="http://mocked_url.com")
    monkeypatch.setattr(
        "src.services.upload.cloudinary.CloudinaryImage",
        lambda public_id: MagicMock(build_url=mock_build_url),
    )

    file = UploadFile(filename="test.png", file=BytesIO(b"test"))
    service = CloudinaryUploadService()
    result = service.upload_file(file=file, username="user1")

    assert result == "http://mocked_url.com"
    mock_build_url.assert_called_once_with(
        width=250, height=250, crop="fill", version="123456"
    )
