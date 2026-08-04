from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.ai_config import clear_api_key, get_api_key, has_api_key, save_api_key
from backend.auth import CurrentUser, get_current_user, require_admin

router = APIRouter(prefix="/api/ai", tags=["ai"])

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_AI_MODEL = "claude-sonnet-5"


class AiKeyRequest(BaseModel):
    api_key: str


class AiMessageRequest(BaseModel):
    model: str = DEFAULT_AI_MODEL
    max_tokens: int = 3000
    system: str | None = None
    messages: list[dict[str, Any]]


@router.get("/config-status")
def ai_config_status() -> dict[str, bool]:
    return {"configured": has_api_key()}


@router.post("/config")
def ai_config_set(payload: AiKeyRequest, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    require_admin(current_user)
    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key không được để trống.")
    save_api_key(payload.api_key)
    return {"configured": True}


@router.delete("/config")
def ai_config_delete(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    require_admin(current_user)
    clear_api_key()
    return {"configured": False}


@router.post("/messages")
async def ai_messages(
    payload: AiMessageRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=412,
            detail="Chưa cấu hình Anthropic API key. Vào Cài đặt AI để thêm.",
        )
    body: dict[str, Any] = {
        "model": payload.model,
        "max_tokens": payload.max_tokens,
        "messages": payload.messages,
    }
    if payload.system:
        body["system"] = payload.system
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                json=body,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Không kết nối được tới Anthropic API: {exc}") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
