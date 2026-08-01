from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_CONFIG_DIR = PROJECT_ROOT / "config"
AI_CONFIG_PATH = AI_CONFIG_DIR / "ai_config.json"


def get_api_key() -> str:
    env_key = os.environ.get("CT388_ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key
    if AI_CONFIG_PATH.exists():
        try:
            data = json.loads(AI_CONFIG_PATH.read_text(encoding="utf-8"))
            return str(data.get("anthropic_api_key", "")).strip()
        except Exception:
            return ""
    return ""


def has_api_key() -> bool:
    return bool(get_api_key())


def save_api_key(api_key: str) -> None:
    AI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    AI_CONFIG_PATH.write_text(
        json.dumps({"anthropic_api_key": api_key.strip()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_api_key() -> None:
    if AI_CONFIG_PATH.exists():
        AI_CONFIG_PATH.unlink()
