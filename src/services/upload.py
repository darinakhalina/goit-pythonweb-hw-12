import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from abc import ABC, abstractmethod

from src.conf.config import settings


class BasicUploadService(ABC):
    @abstractmethod
    def upload_file(self, file: UploadFile, username: str) -> str:
        pass


class CloudinaryUploadService(BasicUploadService):
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    def upload_file(self, file, username) -> str:
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url


class UploadService(BasicUploadService):
    def __init__(self, service: BasicUploadService):
        self.service = service

    def upload_file(self, file, username) -> str:
        return self.service.upload_file(file, username)
