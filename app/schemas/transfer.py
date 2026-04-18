from decimal import Decimal

from pydantic import BaseModel, field_validator


class TransferRequest(BaseModel):
    recipient_account_number: str
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class TransferResponse(BaseModel):
    sender_account_number: str
    recipient_account_number: str
    amount: Decimal
    fee: Decimal
    sender_balance: Decimal
