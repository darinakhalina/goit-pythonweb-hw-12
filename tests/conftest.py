import asyncio
from unittest.mock import MagicMock, AsyncMock, Mock
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import redis.asyncio as redis

from main import app
from src.database.models import Base, User
from src.database.db import get_db
from src.services.auth import create_access_token, Hash

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "id": 1,
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "12345678",
    "role": "admin",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_user["password"])
            current_user = User(
                id=test_user["id"],
                username=test_user["username"],
                email=test_user["email"],
                password=hash_password,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=test_user["role"],
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope="module")
def client_fail_healthchecker():
    async def mock_get_db():
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=Mock(return_value=None))
        )
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token():
    token = await create_access_token(payload={"sub": test_user["username"]})
    return token


@pytest_asyncio.fixture()
async def get_reset_token():
    token = await create_access_token(payload={"sub": test_user["email"]})
    return token


@pytest.fixture(scope="module", autouse=True)
def mock_redis_client():
    from src.services.cache import redis_client

    mock_redis = AsyncMock(spec=redis.Redis)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)

    redis_client.get = mock_redis.get
    redis_client.set = mock_redis.set

    yield mock_redis
