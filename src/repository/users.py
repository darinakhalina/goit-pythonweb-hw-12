from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        user = await self.db.execute(select(User).filter(User.id == user_id))
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        user = await self.db.execute(select(User).filter(User.username == username))
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        user = await self.db.execute(select(User).filter(User.email == email))
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: Optional[str] = None) -> User:
        new_user = User(**body.model_dump(exclude_unset=True), avatar=avatar)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def update_avatar_url(self, email: str, url: str) -> User | None:
        user = await self.get_user_by_email(email)

        if user:
            setattr(user, "avatar", url)
            await self.db.commit()
            await self.db.refresh(user)
            return user

    async def verify_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)

        if user:
            setattr(user, "confirmed", True)
            await self.db.commit()

    async def update_user(self, user: User, body: UserUpdate) -> bool:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return True
