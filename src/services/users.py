from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.database.models import User
from src.schemas.users import UserCreate, UserUpdate
from src.exceptions.exceptions import (
    HTTPNotFoundException,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        user = await self.repository.get_user_by_id(user_id)

        if not user:
            raise HTTPNotFoundException("Not found")

        return user

    async def get_user_by_username(self, username: str):
        user = await self.repository.get_user_by_username(username)
        return user

    async def get_user_by_email(self, email: str):
        user = await self.repository.get_user_by_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        user = await self.get_user_by_email(email)

        if not user:
            raise HTTPNotFoundException("Not found")

        return await self.repository.update_avatar_url(email, url)

    async def verify_email(self, email: str):
        await self.repository.verify_email(email)

    async def update_user(self, user: User, body: UserUpdate):
        return await self.repository.update_user(user, body)
