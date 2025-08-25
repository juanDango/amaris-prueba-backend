from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupIn(BaseModel):
    """Esquema para el registro de un nuevo usuario."""
    email: EmailStr
    password: str
    phone_number: Optional[str] = None

class ConfirmIn(BaseModel):
    """Esquema para confirmar el registro de un usuario."""
    email: EmailStr
    confirmation_code: str

class LoginIn(BaseModel):
    """Esquema para el inicio de sesión."""
    email: EmailStr
    password: str