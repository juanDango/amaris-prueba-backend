from pydantic import BaseModel, EmailStr
from enum import Enum

class NotificationOptions(str, Enum):
    """Opciones para enviar las notificaciones"""
    email = "email"
    sms = "sms"

class UserOut(BaseModel):
    """Esquema de salida para los usuarios."""
    id: str
    email: EmailStr
    phone: str
    balance: int
    notif_options: NotificationOptions
