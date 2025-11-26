"""
Schemas Pydantic para Author
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class AuthorBase(BaseModel):
    """Schema base para Author"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    bio: Optional[str] = None


class AuthorCreate(AuthorBase):
    """Schema para criação de Author"""
    pass


class Author(AuthorBase):
    """Schema completo de Author (com ID)"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
