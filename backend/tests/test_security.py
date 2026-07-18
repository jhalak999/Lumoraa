import pytest

from app.core.exceptions import InvalidCredentialsError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    plain = "SuperSecret123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_token_roundtrip():
    user_id = "11111111-1111-1111-1111-111111111111"
    token = create_access_token(user_id)
    subject = decode_token(token, TokenType.ACCESS)
    assert subject == user_id


def test_refresh_token_rejected_as_access_token():
    user_id = "11111111-1111-1111-1111-111111111111"
    refresh = create_refresh_token(user_id)
    with pytest.raises(InvalidCredentialsError):
        decode_token(refresh, TokenType.ACCESS)


def test_garbage_token_rejected():
    with pytest.raises(InvalidCredentialsError):
        decode_token("not-a-real-jwt", TokenType.ACCESS)
