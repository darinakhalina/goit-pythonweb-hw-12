import json

from typing import Optional

import redis.asyncio as redis

from src.database.models import User
from src.conf.config import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
)


async def update_cached_current_user(user: User) -> None:
    """
    Caches the current user's data in Redis.

    Args:
        user (User): The user object containing user data to cache.

    Returns:
        None
    """
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "avatar": user.avatar,
        "confirmed": user.confirmed,
    }

    await redis_client.set(f"user:{user.username}", json.dumps(user_data), ex=60)


async def get_cached_current_user(username: str) -> Optional[User]:
    """
    Retrieves cached user data from Redis based on the provided username.

    Args:
        username (str): The username used as the Redis cache key.

    Returns:
        Optional[User]: A User object if found and successfully decoded, otherwise None.
    """
    user_data = await redis_client.get(f"user:{username}")

    if user_data:
        try:
            data = json.loads(user_data)
            return User(
                id=data.get("id"),
                username=data.get("username"),
                email=data.get("email"),
                role=data.get("role"),
                avatar=data.get("avatar"),
                confirmed=data.get("confirmed", False),
            )
        except json.JSONDecodeError as e:
            print(f"Failed to decode user data from cache: {e}")
            return None

    return None
