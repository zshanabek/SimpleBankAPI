from datetime import datetime

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User


def get_account(user: User, db: Session) -> Account:
    return db.query(Account).filter(Account.user_id == user.id).first()


def get_transactions(
    user: User,
    db: Session,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[Transaction]:
    account = get_account(user, db)
    query = db.query(Transaction).filter(Transaction.account_id == account.id)
    if from_date:
        query = query.filter(Transaction.created_at >= from_date)
    if to_date:
        query = query.filter(Transaction.created_at <= to_date)
    return query.order_by(Transaction.created_at.desc()).all()
