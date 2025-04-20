from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Get a User by their ID.

        Args:
            user_id (int): The ID of the User to retrieve.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        user = await self.db.execute(select(User).filter(User.id == user_id))
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Get a User by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        user = await self.db.execute(select(User).filter(User.username == username))
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Get a User by their email address.

        Args:
            email (str): The email of the user to retrieve.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        user = await self.db.execute(select(User).filter(User.email == email))
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: Optional[str] = None) -> User:
        """
        Create a new User and save them to the database.

        Args:
            body (UserCreate): The User data to be used for creating the new user.
            avatar (Optional[str], optional): The avatar URL for the user (default is None).

        Returns:
            User: The created User object with their details, including the avatar if provided.
        """
        new_user = User(**body.model_dump(exclude_unset=True), avatar=avatar)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def update_avatar_url(self, email: str, url: str) -> User | None:
        """
        Update the avatar URL for a user identified by their email.

        Args:
            email (str): The email of the user whose avatar URL is to be updated.
            url (str): The new avatar URL to be set for the user.

        Returns:
            User | None: The updated user object if the user exists and the avatar URL is updated,
            or None if the user does not exist.
        """
        user = await self.get_user_by_email(email)

        if user:
            setattr(user, "avatar", url)
            await self.db.commit()
            await self.db.refresh(user)
            return user

    async def verify_email(self, email: str) -> None:
        """
        Verify the email of a user by updating the `confirmed` field to `True`.

        Args:
            email (str): The email of the user to be verified.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)

        if user:
            setattr(user, "confirmed", True)
            await self.db.commit()

    async def update_user(self, user: User, body: UserUpdate) -> bool:
        """
        Update the details of an existing User in the database.

        Args:
            user (User): The user to be updated.
            body (UserUpdate): The data to update the user with.

        Returns:
            bool: Returns `True` if the update was successful.
        """
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return True
