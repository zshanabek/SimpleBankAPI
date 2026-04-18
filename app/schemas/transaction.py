from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.transaction import TransactionType


class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    type: TransactionType
    created_at: datetime

    model_config = {"from_attributes": True}
