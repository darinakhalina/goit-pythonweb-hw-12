import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactBase, ContactUpdate


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user():
    return User(id=1, username="Mock", email="testuser@example.com", role="admin")


@pytest.fixture
def contacts_repository(mock_session, user):
    return ContactsRepository(mock_session, user)


@pytest.mark.asyncio
async def test_get_all(contacts_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            first_name="Test",
            last_name="Mock",
            email="test@example.com",
            phone="1111",
            birthday="1980-01-01",
            user=user,
        )
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)
    contacts = await contacts_repository.get_all()

    assert len(contacts) == 1
    assert contacts[0].first_name == "Test"
    assert contacts[0].last_name == "Mock"
    assert contacts[0].email == "test@example.com"
    assert contacts[0].phone == "1111"
    assert contacts[0].birthday == "1980-01-01"


@pytest.mark.asyncio
async def test_get_contact_by_email(contacts_repository, mock_session, user):
    mock_email = "test@example.com"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        first_name="Test",
        last_name="Mock",
        email=mock_email,
        phone="1111",
        birthday="1980-01-01",
        user=user,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)
    contact = await contacts_repository.get_contact_by_email(email=mock_email)

    assert contact is not None
    assert contact.id == 1
    assert contact.email == mock_email


@pytest.mark.asyncio
async def test_get_contact_by_id(contacts_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        first_name="Test",
        last_name="Mock",
        email="test@example.com",
        phone="1111",
        birthday="1980-01-01",
        user=user,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)
    contact = await contacts_repository.get_contact_by_id(contact_id=1)

    assert contact is not None
    assert contact.id == 1
    assert contact.first_name == "Test"


@pytest.mark.asyncio
async def test_create(contacts_repository, mock_session):
    contact_data = ContactBase(
        first_name="Test",
        last_name="Mock",
        email="test@example.com",
        phone="1111",
        birthday="1980-01-01",
    )
    result = await contacts_repository.create(body=contact_data)

    assert isinstance(result, Contact)
    assert result.first_name == "Test"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update(contacts_repository, mock_session, user):
    contact_data = ContactUpdate(
        first_name="Updated Test",
        last_name="Mock",
        email="test@example.com",
        phone="1111",
    )
    existing_contact = Contact(
        id=1,
        first_name="Test",
        last_name="Mock",
        email="test@example.com",
        phone="1111",
        birthday="1980-01-01",
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)
    result = await contacts_repository.update(contact_id=1, body=contact_data)

    assert result is not None
    assert result.first_name == "Updated Test"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_contact)


@pytest.mark.asyncio
async def test_delete(contacts_repository, mock_session, user):
    existing_tag = Contact(
        id=1,
        first_name="Test To Delete",
        last_name="Mock",
        email="test@example.com",
        phone="1111",
        birthday="1980-01-01",
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_tag
    mock_session.execute = AsyncMock(return_value=mock_result)
    result = await contacts_repository.delete(contact_id=1)

    assert result is not None
    assert result.first_name == "Test To Delete"
    mock_session.delete.assert_awaited_once_with(existing_tag)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_birthdays_within_days_same_year():
    contacts = [
        Contact(first_name="John", birthday=datetime(1990, 4, 16).date()),
        Contact(first_name="Jane", birthday=datetime(1990, 4, 20).date()),
        Contact(first_name="Alice", birthday=datetime(1990, 4, 25).date()),
    ]
    user = MagicMock(id=1)
    mock_session = MagicMock()

    async def mock_execute(query):
        today = datetime(2023, 4, 15).date()
        week = today + timedelta(days=7)
        today_mmdd = today.strftime("%m-%d")
        week_mmdd = week.strftime("%m-%d")

        filtered = [
            c
            for c in contacts
            if today_mmdd <= c.birthday.strftime("%m-%d") <= week_mmdd
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = filtered
        return mock_result

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    repo = ContactsRepository(mock_session, user)

    with patch("src.repository.contacts.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 4, 15)
        result = await repo.get_all(birthdays_within_days=7)

    assert len(result) == 2
    assert {c.first_name for c in result} == {"John", "Jane"}


@pytest.mark.asyncio
async def test_get_all_with_skip():
    contacts = [
        Contact(first_name="John"),
        Contact(first_name="Jane"),
        Contact(first_name="Alice"),
    ]
    user = MagicMock(id=1)
    mock_session = MagicMock()

    async def mock_execute(query):
        filtered = contacts[1:]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = filtered
        return mock_result

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    repo = ContactsRepository(mock_session, user)

    result = await repo.get_all(skip=1)

    assert len(result) == 2
    assert {c.first_name for c in result} == {"Jane", "Alice"}


@pytest.mark.asyncio
async def test_get_all_with_limit():
    contacts = [
        Contact(first_name="John"),
        Contact(first_name="Jane"),
        Contact(first_name="Alice"),
    ]
    user = MagicMock(id=1)
    mock_session = MagicMock()

    async def mock_execute(query):
        filtered = contacts[:2]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = filtered
        return mock_result

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    repo = ContactsRepository(mock_session, user)

    result = await repo.get_all(limit=2)

    assert len(result) == 2
    assert {c.first_name for c in result} == {"John", "Jane"}


@pytest.mark.asyncio
async def test_get_all_birthdays_across_new_year():
    contacts = [
        Contact(first_name="John", birthday=datetime(1990, 12, 29).date()),
        Contact(first_name="Jane", birthday=datetime(1990, 1, 2).date()),
        Contact(first_name="Alice", birthday=datetime(1990, 1, 10).date()),
    ]
    user = MagicMock(id=1)
    mock_session = MagicMock()

    async def mock_execute(query):
        today = datetime(2023, 12, 28).date()
        week = today + timedelta(days=7)
        today_mmdd = today.strftime("%m-%d")
        week_mmdd = week.strftime("%m-%d")

        filtered = [
            c
            for c in contacts
            if c.birthday.strftime("%m-%d") >= today_mmdd
            or c.birthday.strftime("%m-%d") <= week_mmdd
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = filtered
        return mock_result

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    repo = ContactsRepository(mock_session, user)

    with patch("src.repository.contacts.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 12, 28)
        result = await repo.get_all(birthdays_within_days=7)

    assert len(result) == 2
    assert {c.first_name for c in result} == {"John", "Jane"}
