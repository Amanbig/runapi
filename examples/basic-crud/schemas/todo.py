"""Request/response shapes. FastAPI validates incoming JSON against these."""

from typing import Optional

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    done: bool = False


class TodoUpdate(BaseModel):
    """Every field is optional so PUT can change just one of them."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    done: Optional[bool] = None
