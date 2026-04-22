from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.transfer import TransferRequest, TransferResponse

FEE_RATE = Decimal("0.025")
FEE_MINIMUM = Decimal("5.00")


def calculate_fee(amount: Decimal) -> Decimal:
    return max(amount * FEE_RATE, FEE_MINIMUM).quantize(Decimal("0.01"))


def transfer_funds(data: TransferRequest, sender: User, db: Session) -> TransferResponse:
    # Unlocked pre-read to resolve IDs and catch obvious errors before acquiring locks
    sender_account = db.query(Account).filter(Account.user_id == sender.id).first()
    if sender_account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender account not found")

    # Check before querying recipient to avoid a wasted DB round-trip
    if sender_account.account_number == data.recipient_account_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to own account")

    recipient_account = (
        db.query(Account)
        .filter(Account.account_number == data.recipient_account_number)
        .first()
    )
    if recipient_account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient account not found")

    # Acquire row-level locks in ascending id order to prevent deadlocks when two
    # users transfer to each other simultaneously (A→B and B→A would otherwise deadlock)
    locked = (
        db.query(Account)
        .filter(Account.id.in_([sender_account.id, recipient_account.id]))
        .with_for_update()
        .order_by(Account.id)
        .all()
    )
    locked_by_id = {a.id: a for a in locked}
    # Guard against an account being deleted between the pre-read and the lock
    if len(locked_by_id) != 2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account no longer exists")
    sender_account = locked_by_id[sender_account.id]
    recipient_account = locked_by_id[recipient_account.id]

    fee = calculate_fee(data.amount)
    total_debit = data.amount + fee

    if sender_account.balance < total_debit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds (need {total_debit}, have {sender_account.balance})",
        )

    sender_account.balance -= total_debit
    recipient_account.balance += data.amount

    db.add(Transaction(account_id=sender_account.id, amount=total_debit, type=TransactionType.debit))
    db.add(Transaction(account_id=recipient_account.id, amount=data.amount, type=TransactionType.credit))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transfer failed")
    db.refresh(sender_account)

    return TransferResponse(
        sender_account_number=sender_account.account_number,
        recipient_account_number=recipient_account.account_number,
        amount=data.amount,
        fee=fee,
        sender_balance=sender_account.balance,
    )
