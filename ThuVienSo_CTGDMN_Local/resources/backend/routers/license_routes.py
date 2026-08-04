from typing import Any

from fastapi import APIRouter

from backend.license_manager import create_license_for_current_machine, get_license_status, get_machine_id

router = APIRouter(tags=["license"])


# ─── Legacy desktop machine-lock license (single-install offline mode) ─────
@router.get("/api/license/status")
def license_status() -> dict[str, Any]:
    return get_license_status()


@router.get("/api/license/machine-id")
def license_machine_id() -> dict[str, str]:
    return {"machine_id": get_machine_id()}


@router.post("/api/license/create-demo")
def license_create_demo() -> dict[str, Any]:
    data = create_license_for_current_machine()
    status = get_license_status()
    return {"status": "ok", "license": data, "license_status": status}
