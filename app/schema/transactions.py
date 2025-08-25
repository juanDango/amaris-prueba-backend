from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class TransactionType(str, Enum):
    """Tipo de transacción."""

    SUBSCRIBE = "subscribe"
    CANCEL = "cancel"

class TransactionIn(BaseModel):
    """Esquema de entrada para crear una transacción."""
    fund_id: str
    transaction_type: TransactionType
    amount: int | None

class Transaction(BaseModel):
    """Esquema de una transacción."""
    id: str
    user_id: str
    fund_id: str
    amount: int
    transaction_type: TransactionType
    timestamp: datetime