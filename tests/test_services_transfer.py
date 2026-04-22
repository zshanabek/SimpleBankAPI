from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.account import Account
from app.models.user import User
from app.schemas.transfer import TransferRequest
from app.services.transfer import calculate_fee, transfer_funds


def _make_db(sender_acc, recipient_acc):
    """Build a MagicMock db that handles both the pre-read .first() calls
    and the locking .with_for_update().order_by().all() call."""
    db = MagicMock()
    filter_mock = db.query.return_value.filter.return_value
    filter_mock.first.side_effect = [sender_acc, recipient_acc]
    filter_mock.with_for_update.return_value.order_by.return_value.all.return_value = (
        sorted([sender_acc, recipient_acc], key=lambda a: a.id)
    )
    return db


def test_fee_minimum():
    assert calculate_fee(Decimal("100")) == Decimal("5.00")


def test_fee_percentage():
    assert calculate_fee(Decimal("400")) == Decimal("10.00")


def test_fee_exactly_at_minimum_boundary():
    assert calculate_fee(Decimal("200")) == Decimal("5.00")


def test_transfer_success():
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("1000"), user_id=1)
    recipient_acc = Account(id=2, account_number="2222222222", balance=Decimal("0"), user_id=2)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")
    db = _make_db(sender_acc, recipient_acc)

    result = transfer_funds(
        TransferRequest(recipient_account_number="2222222222", amount=Decimal("100")),
        sender_user,
        db,
    )

    assert result.fee == Decimal("5.00")
    assert sender_acc.balance == Decimal("895.00")
    assert recipient_acc.balance == Decimal("100.00")


def test_transfer_insufficient_funds():
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("10"), user_id=1)
    recipient_acc = Account(id=2, account_number="2222222222", balance=Decimal("0"), user_id=2)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")
    db = _make_db(sender_acc, recipient_acc)

    with pytest.raises(HTTPException) as exc:
        transfer_funds(
            TransferRequest(recipient_account_number="2222222222", amount=Decimal("100")),
            sender_user,
            db,
        )

    assert exc.value.status_code == 400


def test_transfer_to_own_account_raises():
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("1000"), user_id=1)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = sender_acc

    with pytest.raises(HTTPException) as exc:
        transfer_funds(
            TransferRequest(recipient_account_number="1111111111", amount=Decimal("100")),
            sender_user,
            db,
        )

    assert exc.value.status_code == 400


def test_transfer_negative_amount_raises():
    with pytest.raises(ValueError):
        TransferRequest(recipient_account_number="2222222222", amount=Decimal("-50"))


def test_transfer_under_comission_fee():
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("100"), user_id=1)
    recipient_acc = Account(id=2, account_number="2222222222", balance=Decimal("0"), user_id=2)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")
    db = _make_db(sender_acc, recipient_acc)

    result = transfer_funds(
        TransferRequest(recipient_account_number="2222222222", amount=Decimal("3")),
        sender_user,
        db,
    )

    assert result.fee == Decimal("5.00")
    assert sender_acc.balance == Decimal("92.00")
    assert recipient_acc.balance == Decimal("3.00")
