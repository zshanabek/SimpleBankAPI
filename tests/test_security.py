import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)


def test_verify_wrong_password():
    hashed = hash_password("secret123")
    assert not verify_password("wrong", hashed)


def test_hash_is_not_plaintext():
    assert hash_password("secret123") != "secret123"


def test_create_and_decode_token():
    token = create_access_token("user@example.com")
    assert decode_access_token(token) == "user@example.com"


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.token")
