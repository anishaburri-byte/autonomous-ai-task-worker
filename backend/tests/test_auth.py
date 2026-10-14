from app.auth import create_token, require_user, sign_approval, verify_approval
import pytest
# pyrefly: ignore [missing-import]
from fastapi import HTTPException

def test_jwt_roundtrip():
    tok=create_token("demo-user")
    assert require_user(f"Bearer {tok}")=="demo-user"

def test_invalid_token():
    try:
        require_user("Bearer invalid")
        assert False
    except HTTPException as e:
        assert e.status_code==401

def test_approval_token():
    tok=sign_approval(123, "abc_hash")
    assert verify_approval(tok,123,"abc_hash")==True
    assert verify_approval(tok,123,"wrong")==False
    assert verify_approval(tok,999,"abc_hash")==False
