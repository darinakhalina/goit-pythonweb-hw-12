from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db
from src.exceptions.exceptions import (
    HTTPInternalDatabaseException,
    HTTPInternalUnexpectedException,
)

router = APIRouter(tags=["utils"])


@router.get("/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPInternalDatabaseException("Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        raise HTTPInternalUnexpectedException(f"Error connecting to the database: {e}")
