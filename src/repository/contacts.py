from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_, and_, func

from src.database.models import Contact
from src.schemas.contacts import ContactBase, ContactUpdate
from src.schemas.users import UserBase


class ContactsRepository:
    current_user: UserBase

    def __init__(self, session: AsyncSession, user: UserBase):
        self.db = session
        self.current_user = user

    async def get_all(
        self,
        birthdays_within_days: int | None = None,
        search: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ):
        stmt = select(Contact)

        if search is not None:
            stmt = stmt.filter(
                or_(
                    Contact.first_name.ilike(f"%{search}%"),
                    Contact.last_name.ilike(f"%{search}%"),
                    Contact.email.ilike(f"%{search}%"),
                )
            )

        if birthdays_within_days is not None:
            today = datetime.now().date()
            week = today + timedelta(days=birthdays_within_days)

            today_mmdd = today.strftime("%m-%d")
            week_mmdd = week.strftime("%m-%d")

            if today_mmdd <= week_mmdd:
                stmt = stmt.filter(
                    func.to_char(Contact.birthday, "MM-DD").between(
                        today_mmdd, week_mmdd
                    )
                )
            else:
                stmt = stmt.filter(
                    or_(
                        func.to_char(Contact.birthday, "MM-DD") >= today_mmdd,
                        func.to_char(Contact.birthday, "MM-DD") <= week_mmdd,
                    )
                )

        if skip is not None:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        stmt = stmt.filter(and_(Contact.user == self.current_user))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_email(
        self,
        email: str,
    ) -> Contact | None:
        return (
            await self.db.execute(
                select(Contact).filter(
                    and_(Contact.email == email, Contact.user == self.current_user)
                )
            )
        ).scalar_one_or_none()

    async def get_contact_by_id(
        self,
        contact_id: int,
    ) -> Contact | None:
        return (
            await self.db.execute(
                select(Contact).filter(
                    and_(Contact.id == contact_id, Contact.user == self.current_user)
                )
            )
        ).scalar_one_or_none()

    async def create(self, body: ContactBase):
        contact = Contact(**body.model_dump(), user_id=self.current_user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update(self, contact_id: int, body: ContactUpdate):
        contact = await self.get_contact_by_id(contact_id)

        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)
            return contact

    async def delete(self, contact_id: int):
        contact = await self.get_contact_by_id(contact_id)

        if contact:
            await self.db.delete(contact)
            await self.db.commit()
            return contact
