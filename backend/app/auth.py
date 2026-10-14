import os, jwt, datetime
from datetime import timezone

# pyrefly: ignore [missing-import]
from fastapi import Header, HTTPException
from itsdangerous import URLSafeTimedSerializer

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-prod-32chars")
signer = URLSafeTimedSerializer(SECRET)

def create_token(user_id: str):
    return jwt.encode({"sub": user_id, "exp": datetime.datetime.now(timezone.utc)+datetime.timedelta(days=7)}, SECRET, algorithm="HS256")

def require_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def sign_approval(task_id: int, payload_hash: str) -> str:
    return signer.dumps({"task_id": task_id, "hash": payload_hash})

def verify_approval(token: str, task_id: int, payload_hash: str) -> bool:
    try:
        data = signer.loads(token, max_age=3600)
        return data["task_id"]==task_id and data["hash"]==payload_hash
    except Exception:
        return False
