from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactBase, ContactUpdate
from src.schemas.users import UserBase
from src.exceptions.exceptions import (
    HTTPNotFoundException,
    HTTPConflictRequestException,
)


class ContactsService:
    repository: ContactsRepository
    current_user: UserBase

    def __init__(self, db: AsyncSession, user: UserBase):
        self.repository = ContactsRepository(db, user)
        self.current_user = user

    async def get_all(
        self,
        search: str | None = None,
        birthdays_within_days: int | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ):

        return await self.repository.get_all(
            search=search,
            birthdays_within_days=birthdays_within_days,
            skip=skip,
            limit=limit,
        )

    async def get_by_id(self, contact_id: int):
        contact = await self.repository.get_contact_by_id(contact_id)

        if contact is None:
            raise HTTPNotFoundException("Not found")

        return contact

    async def create(self, body: ContactBase):
        contact = await self.repository.get_contact_by_email(body.email)

        if contact:
            raise HTTPConflictRequestException(
                "Cannot create contact, email already registered."
            )

        return await self.repository.create(body)

    async def update_by_id(self, contact_id: int, body: ContactUpdate):
        contact = await self.repository.get_contact_by_id(contact_id)

        if not contact:
            raise HTTPNotFoundException("Not found")

        return await self.repository.update(contact_id, body)

    async def delete_by_id(self, contact_id: int):
        contact = await self.repository.get_contact_by_id(contact_id)

        if contact is None:
            raise HTTPNotFoundException("Not found")

        return await self.repository.delete(contact_id)
