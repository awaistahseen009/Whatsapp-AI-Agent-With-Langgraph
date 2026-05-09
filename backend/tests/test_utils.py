from src.app.utils.utils import (
    generate_hash_password,
    verify_password,
    create_access_token,
    decode_token,
)

def test_generate_hash_password():
    password = "MySecurePassword123"
    hashed = generate_hash_password(password)
    assert hashed != password
    assert isinstance(hashed, str)
    assert hashed.startswith("$2b$")

def test_verify_password_correct():
    password = "MySecurePassword123"
    hashed = generate_hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    password = "MySecurePassword123"
    hashed = generate_hash_password(password)
    assert verify_password("WrongPassword!", hashed) is False

def test_create_access_token():
    user_data = {"user_id": "123", "role": "owner"}
    token = create_access_token(user_data)
    assert isinstance(token, str)
    assert len(token) > 20

def test_decode_token():
    user_data = {"user_id": "123", "role": "owner"}
    token = create_access_token(user_data)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["user"]["user_id"] == "123"
    assert decoded["user"]["role"] == "owner"
    assert "expiry" in decoded
    assert "jti" in decoded

def test_decode_token_invalid():
    decoded = decode_token("invalid.jwt.token")
    assert decoded is None
