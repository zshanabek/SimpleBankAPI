from decimal import Decimal

from pydantic import BaseModel


class BalanceResponse(BaseModel):
    account_number: str
    balance: Decimal

    model_config = {"from_attributes": True}
