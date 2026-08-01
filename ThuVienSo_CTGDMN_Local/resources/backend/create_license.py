from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from backend.license_manager import LICENSE_PATH, create_license_for_current_machine, get_machine_id


def ask(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def main() -> None:
    print("CT388 Local App - tạo license offline cho máy hiện tại")
    print("Mã máy:", get_machine_id())
    owner = ask("Chủ sở hữu", "CT388 Demo User")
    school_name = ask("Tên trường", "Trường mầm non demo")
    valid_until = ask("Hạn dùng YYYY-MM-DD", "2026-08-04")
    data = create_license_for_current_machine(owner=owner, school_name=school_name, valid_until=valid_until)
    print("Đã tạo license:", LICENSE_PATH)
    print("Trường:", data["school_name"])
    print("Chủ sở hữu:", data["owner"])
    print("Hạn dùng:", data["valid_until"])


if __name__ == "__main__":
    main()