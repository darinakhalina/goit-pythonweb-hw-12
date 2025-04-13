from fastapi import APIRouter, Depends, File, UploadFile, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db

from src.schemas.users import UserBase
from src.services.auth import get_current_user, get_current_user_admin
from src.services.users import UserService
from src.services.upload import UploadService, CloudinaryUploadService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me", response_model=UserBase, description="Limited to 10 requests per minute."
)
@limiter.limit("10/minute")
async def me(request: Request, user: UserBase = Depends(get_current_user)):
    return user


@router.patch("/avatar", response_model=UserBase)
async def update_avatar_user(
    file: UploadFile = File(),
    user: UserBase = Depends(get_current_user_admin),
    db: AsyncSession = Depends(get_db),
):
    upload_service = UploadService(CloudinaryUploadService())
    avatar_url = upload_service.upload_file(file, user.username)
    user_service = UserService(db)

    return await user_service.update_avatar_url(user.email, avatar_url)
