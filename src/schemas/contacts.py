from datetime import date
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from src.exceptions.exceptions import HTTPBadRequestException


def validate_birthday(birthday: str):
    try:
        date.fromisoformat(birthday)
    except ValueError:
        raise HTTPBadRequestException("Invalid date format. Should be YYYY-MM-DD.")


class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=200)
    phone: str = Field(min_length=3, max_length=50)
    birthday: str

    @field_validator("birthday", mode="before")
    @classmethod
    def validate_birthday_field(cls, v):
        if v:
            validate_birthday(v)
        return v


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=180)
    phone: str | None = Field(default=None, min_length=3, max_length=80)
    birthday: str | None = None

    @field_validator("birthday", mode="before")
    @classmethod
    def validate_birthday_field(cls, v):
        if v:
            validate_birthday(v)
        return v


class ContactResponse(ContactBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
