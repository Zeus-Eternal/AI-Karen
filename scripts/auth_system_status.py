#!/usr/bin/env python3
"""Authentication System Status Check for Kari AI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

PRODUCTION_FILES = [
    "src/auth/auth_service.py",
    "src/auth/auth_middleware.py",
    "src/auth/auth_routes.py",
]

BACKUP_DIR = Path("backups/complex_auth_system")
USERS_FILE = Path("data/users.json")


def describe_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    size_kb = path.stat().st_size / 1024
    modified = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    return f"{size_kb:.1f} KiB, updated {modified}"


def main() -> None:
    print("🔐 Authentication System Status")
    print("=" * 50)

    project_root = Path(__file__).resolve().parent.parent

    print("📁 Production Auth Components:")
    for relative in PRODUCTION_FILES:
        status = describe_file(project_root / relative)
        icon = "✅" if status != "missing" else "❌"
        print(f"  {icon} {relative} → {status}")

    print("\n👤 User Store:")
    users_path = project_root / USERS_FILE
    if users_path.exists():
        try:
            with users_path.open("r", encoding="utf-8") as handle:
                users = json.load(handle)
            print(f"  ✅ data/users.json ({len(users)} users)")
            for email, info in users.items():
                roles = ", ".join(info.get("roles", [])) or "—"
                verified = "✅" if info.get("is_verified", False) else "⚠️"
                print(f"     {verified} {email} [{roles}]")
        except Exception as exc:  # pragma: no cover - diagnostics only
            print(f"  ❌ Failed to read users.json: {exc}")
    else:
        print("  ❌ data/users.json (missing)")

    print("\n🗃️  Legacy Auth Backup:")
    if BACKUP_DIR.exists():
        files = list(BACKUP_DIR.glob("**/*.py"))
        print(f"  ✅ backup present with {len(files)} Python files")
    else:
        print("  ⚠️ complex auth backup not found")

    print("\n📌 Next Steps:")
    print("  1. Export NEXT_PUBLIC_API_URL to point at the production backend.")
    print("  2. Run `python tests/manual/test_auth_debug.py` to validate login.")
    print("  3. Rotate JWT secrets before enabling external access.")


if __name__ == "__main__":
    main()
