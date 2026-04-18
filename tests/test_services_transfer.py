from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.account import Account
from app.models.user import User
from app.schemas.transfer import TransferRequest
from app.services.transfer import calculate_fee, transfer_funds


def test_fee_minimum():
    assert calculate_fee(Decimal("100")) == Decimal("5.00")


def test_fee_percentage():
    assert calculate_fee(Decimal("400")) == Decimal("10.00")


def test_fee_exactly_at_minimum_boundary():
    # 2.5% of 200 = 5.00 — exactly at minimum
    assert calculate_fee(Decimal("200")) == Decimal("5.00")


def _make_transfer_db(sender_balance: Decimal, same_account: bool = False):
    sender = Account(id=1, account_number="1111111111", balance=sender_balance, user_id=1)
    recipient_number = "1111111111" if same_account else "2222222222"
    recipient = Account(id=2, account_number=recipient_number, balance=Decimal("0"), user_id=2)

    db = MagicMock()

    def query_side_effect(model):
        mock = MagicMock()
        if model is Account:
            def filter_side_effect(*args):
                inner = MagicMock()
                inner.first.return_value = sender if "user_id" in str(args) else recipient
                return inner
            mock.filter.side_effect = filter_side_effect
        return mock

    db.query.side_effect = query_side_effect
    return db, sender, recipient


def test_transfer_success():
    db = MagicMock()
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("1000"), user_id=1)
    recipient_acc = Account(id=2, account_number="2222222222", balance=Decimal("0"), user_id=2)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")

    db.query.return_value.filter.return_value.first.side_effect = [
        sender_acc, recipient_acc
    ]

    result = transfer_funds(
        TransferRequest(recipient_account_number="2222222222", amount=Decimal("100")),
        sender_user,
        db,
    )

    assert result.fee == Decimal("5.00")
    assert sender_acc.balance == Decimal("895.00")
    assert recipient_acc.balance == Decimal("100.00")


def test_transfer_insufficient_funds():
    db = MagicMock()
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("10"), user_id=1)
    recipient_acc = Account(id=2, account_number="2222222222", balance=Decimal("0"), user_id=2)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")

    db.query.return_value.filter.return_value.first.side_effect = [
        sender_acc, recipient_acc
    ]

    with pytest.raises(HTTPException) as exc:
        transfer_funds(
            TransferRequest(recipient_account_number="2222222222", amount=Decimal("100")),
            sender_user,
            db,
        )

    assert exc.value.status_code == 400


def test_transfer_to_own_account_raises():
    db = MagicMock()
    sender_acc = Account(id=1, account_number="1111111111", balance=Decimal("1000"), user_id=1)
    sender_user = User(id=1, email="a@b.com", hashed_password="x")

    db.query.return_value.filter.return_value.first.side_effect = [
        sender_acc, sender_acc
    ]

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
