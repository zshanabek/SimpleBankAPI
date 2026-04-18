from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.account import BalanceResponse
from app.schemas.transaction import TransactionResponse
from app.services.account import get_account, get_transactions

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/balance", response_model=BalanceResponse)
def balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_account(current_user, db)


@router.get("/transactions", response_model=list[TransactionResponse])
def transactions(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transactions(current_user, db, from_date, to_date)
