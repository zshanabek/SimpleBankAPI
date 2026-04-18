from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.account import Account
from app.models.user import User
from app.schemas.user import UserRegister
from app.services.auth import WELCOME_BONUS, login_user, register_user


def _make_db(existing_user=None):
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = existing_user
    return db


def test_register_user_success():
    db = _make_db(existing_user=None)

    with patch("app.services.auth._generate_account_number", return_value="1234567890"):
        user = register_user(UserRegister(email="a@b.com", password="pass"), db)

    db.add.assert_called()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_register_duplicate_email_raises_409():
    db = _make_db(existing_user=User(id=1, email="a@b.com", hashed_password="x"))

    with pytest.raises(HTTPException) as exc:
        register_user(UserRegister(email="a@b.com", password="pass"), db)

    assert exc.value.status_code == 409


def test_register_creates_welcome_bonus_transaction():
    db = MagicMock()
    # First query (duplicate check) returns None; subsequent flush gives account id
    db.query.return_value.filter.return_value.first.return_value = None

    added_objects = []
    db.add.side_effect = lambda obj: added_objects.append(obj)

    with patch("app.services.auth._generate_account_number", return_value="1234567890"):
        register_user(UserRegister(email="new@b.com", password="pass"), db)

    accounts = [o for o in added_objects if isinstance(o, Account)]
    assert len(accounts) == 1
    assert accounts[0].balance == WELCOME_BONUS


def test_login_user_success():
    from app.core.security import hash_password

    user = User(id=1, email="a@b.com", hashed_password=hash_password("pass"))
    db = _make_db(existing_user=user)

    result = login_user("a@b.com", "pass", db)

    assert result.token_type == "bearer"
    assert result.access_token


def test_login_wrong_password_raises_401():
    from app.core.security import hash_password

    user = User(id=1, email="a@b.com", hashed_password=hash_password("correct"))
    db = _make_db(existing_user=user)

    with pytest.raises(HTTPException) as exc:
        login_user("a@b.com", "wrong", db)

    assert exc.value.status_code == 401


def test_login_unknown_email_raises_401():
    db = _make_db(existing_user=None)

    with pytest.raises(HTTPException) as exc:
        login_user("nobody@b.com", "pass", db)

    assert exc.value.status_code == 401
