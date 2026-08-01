from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LICENSE_DIR = PROJECT_ROOT / "license"
LICENSE_PATH = LICENSE_DIR / "license.json"
SECRET_PATH = LICENSE_DIR / "license_secret.txt"
APP_NAME = "CT388 Local App"
SIGNATURE_FIELDS = [
    "app",
    "edition",
    "owner",
    "school_name",
    "machine_id",
    "issued_at",
    "valid_until",
    "max_devices",
]


def _today() -> date:
    return date.today()


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_machine_id() -> str:
    """Return a stable, non-sensitive local machine id for offline licensing."""
    parts = [
        os.environ.get("COMPUTERNAME", ""),
        os.environ.get("USERNAME", ""),
        platform.node() or "",
        platform.machine() or "",
        platform.processor() or "",
        platform.system() or "",
    ]
    raw = "|".join(p.strip().lower() for p in parts if p and p.strip())
    if not raw:
        raw = f"ct388-local-fallback|{PROJECT_ROOT}"
    return _stable_hash(raw)[:32].upper()


def get_secret_key() -> str:
    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    env_secret = os.environ.get("CT388_LICENSE_SECRET", "").strip()
    if env_secret:
        return env_secret
    if SECRET_PATH.exists():
        value = SECRET_PATH.read_text(encoding="utf-8").strip()
        if value:
            return value
    secret = "ct388-demo-" + secrets.token_hex(32)
    SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


def _signature_payload(data: dict[str, Any]) -> str:
    payload = {field: data.get(field, "") for field in SIGNATURE_FIELDS}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sign_license(data: dict[str, Any]) -> str:
    secret = get_secret_key().encode("utf-8")
    payload = _signature_payload(data).encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def load_license(path: Path | None = None) -> dict[str, Any] | None:
    license_path = path or LICENSE_PATH
    if not license_path.exists():
        return None
    try:
        return json.loads(license_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"_load_error": "Không đọc được file license.json"}


def verify_license(data: dict[str, Any] | None = None) -> dict[str, Any]:
    lic = data if data is not None else load_license()
    machine_id = get_machine_id()
    if lic is None:
        return {
            "activated": False,
            "mode": "missing",
            "school_name": "",
            "owner": "",
            "valid_until": "",
            "machine_id": machine_id,
            "message": "Chưa có license",
        }
    if lic.get("_load_error"):
        return {
            "activated": False,
            "mode": "invalid",
            "school_name": "",
            "owner": "",
            "valid_until": "",
            "machine_id": machine_id,
            "message": lic["_load_error"],
        }

    required = [field for field in SIGNATURE_FIELDS if field not in lic]
    if required:
        return _status(False, "invalid", lic, machine_id, "License thiếu trường: " + ", ".join(required))
    if lic.get("app") != APP_NAME:
        return _status(False, "invalid", lic, machine_id, "License không đúng app CT388 Local App.")
    if str(lic.get("machine_id", "")).upper() != machine_id:
        return _status(False, "invalid", lic, machine_id, "License không khớp mã máy hiện tại.")

    expected = sign_license(lic)
    actual = str(lic.get("signature", ""))
    if not actual or not hmac.compare_digest(expected, actual):
        return _status(False, "invalid", lic, machine_id, "Chữ ký license không hợp lệ.")

    valid_until = str(lic.get("valid_until", ""))
    try:
        expire_date = datetime.strptime(valid_until, "%Y-%m-%d").date()
    except ValueError:
        return _status(False, "invalid", lic, machine_id, "Ngày hết hạn license không hợp lệ.")
    if expire_date < _today():
        return _status(False, "expired", lic, machine_id, "License đã hết hạn. App đang chạy ở chế độ DEMO.")

    return _status(True, "activated", lic, machine_id, "Đã kích hoạt license offline cho máy hiện tại.")


def _status(activated: bool, mode: str, lic: dict[str, Any], machine_id: str, message: str) -> dict[str, Any]:
    return {
        "activated": activated,
        "mode": mode,
        "school_name": lic.get("school_name", ""),
        "owner": lic.get("owner", ""),
        "valid_until": lic.get("valid_until", ""),
        "machine_id": machine_id,
        "message": message,
    }


def get_license_status() -> dict[str, Any]:
    return verify_license()


def create_license_for_current_machine(
    owner: str = "CT388 Demo User",
    school_name: str = "Trường mầm non demo",
    valid_until: str | None = None,
    edition: str = "local-offline",
    max_devices: int = 1,
    write_file: bool = True,
) -> dict[str, Any]:
    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    if not valid_until:
        valid_until = (_today() + timedelta(days=30)).isoformat()
    data: dict[str, Any] = {
        "app": APP_NAME,
        "edition": edition,
        "owner": owner,
        "school_name": school_name,
        "machine_id": get_machine_id(),
        "issued_at": _today().isoformat(),
        "valid_until": valid_until,
        "max_devices": max_devices,
    }
    data["signature"] = sign_license(data)
    if write_file:
        LICENSE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data