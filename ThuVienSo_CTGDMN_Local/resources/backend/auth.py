from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTH_SECRET_PATH = PROJECT_ROOT / "config" / "auth_secret.txt"
TOKEN_TTL_SECONDS = 30 * 24 * 3600  # 30 ngày

PBKDF2_ALGO = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 260_000


def get_auth_secret() -> str:
    env_secret = os.environ.get("CT388_AUTH_SECRET", "").strip()
    if env_secret:
        return env_secret
    if AUTH_SECRET_PATH.exists():
        value = AUTH_SECRET_PATH.read_text(encoding="utf-8").strip()
        if value:
            return value
    AUTH_SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    AUTH_SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"{PBKDF2_ALGO}${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        algo, iterations_s, salt, expected_hex = hashed.split("$")
        if algo != PBKDF2_ALGO:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations_s))
        return hmac.compare_digest(digest.hex(), expected_hex)
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: int, school_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "school_id": school_id,
        "role": role,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(get_auth_secret().encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload_b64, signature = token.split(".")
        expected = hmac.new(get_auth_secret().encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


class CurrentUser:
    def __init__(self, user_id: int, school_id: int, role: str):
        self.user_id = user_id
        self.school_id = school_id
        self.role = role


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Chưa đăng nhập. Vui lòng đăng nhập lại.")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")
    return CurrentUser(user_id=payload["user_id"], school_id=payload["school_id"], role=payload["role"])


def require_admin(user: CurrentUser) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ hiệu trưởng/quản trị trường mới thực hiện được thao tác này.")


def require_superadmin(user: CurrentUser) -> None:
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Chỉ quản trị hệ thống mới thực hiện được thao tác này.")


def get_superadmin_credentials() -> tuple[str, str] | None:
    email = os.environ.get("CT388_SUPERADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("CT388_SUPERADMIN_PASSWORD", "").strip()
    if not email or not password:
        return None
    return email, password


def requires_school_approval() -> bool:
    """Chỉ bật hàng rào duyệt trường khi có tài khoản quản trị hệ thống được
    cấu hình (CT388_SUPERADMIN_EMAIL/PASSWORD) — tức là có người thực sự duyệt
    được. Không dựa vào DATABASE_URL vì bản web hosted vẫn có thể chạy tạm bằng
    SQLite (chưa nối Postgres) mà vẫn cần duyệt. Không đặt 2 biến này (mặc định
    của bản desktop) thì đăng ký tự động duyệt ngay — tránh trường hợp đăng ký
    xong rồi kẹt mãi vì không ai duyệt được."""
    return get_superadmin_credentials() is not None
