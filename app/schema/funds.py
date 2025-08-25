from pydantic import BaseModel, EmailStr
from enum import Enum

class FundsCategories(str, Enum):
    """Categorías de fondos disponibles."""
    FPV = "FPV"
    FIC = "FIC"

class FundsOut(BaseModel):
    """Esquema de salida para los fondos."""
    id: int
    name: str
    min_amount: int
    category: FundsCategories
