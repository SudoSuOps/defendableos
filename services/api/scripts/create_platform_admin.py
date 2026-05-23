"""Create the first platform_admin user securely.

Run from the project root (or via flyctl ssh on the live machine):

  # Local dev:
  cd services/api && .venv/bin/python scripts/create_platform_admin.py

  # Production (interactive · prompts privately for password):
  flyctl ssh console --app defendableos-api --command \\
      'python scripts/create_platform_admin.py'

Doctrine:
  · NEVER takes a password as a command-line argument or env var · always
    uses getpass.getpass which reads from /dev/tty without echo
  · NEVER prints the password back · only confirms "user created"
  · NEVER prints the JWT either · operator can issue one via POST /auth/login
    after this script completes
  · Refuses to overwrite an existing user · use a different email
  · Refuses to create a user without is_platform_admin=True (this script
    exists specifically to bootstrap admin access · use regular signup
    flow for non-admin accounts)
  · Enforces a minimum password length of 16 chars (bcrypt is robust but
    long passwords are still better)
"""
from __future__ import annotations

import getpass
import re
import sys
from pathlib import Path

# Allow `python scripts/create_platform_admin.py` from services/api/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402


MIN_PASSWORD_LEN = 16
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _prompt_email() -> str:
    email = input("Admin email: ").strip().lower()
    if not EMAIL_RE.match(email):
        raise SystemExit(f"[refuse] {email!r} does not look like a valid email.")
    return email


def _prompt_name() -> str:
    name = input("Admin display name (e.g. 'DefendableOS Founder'): ").strip()
    if not name:
        raise SystemExit("[refuse] display name is required.")
    return name[:255]


def _prompt_password() -> str:
    # getpass reads from /dev/tty without echo · NOT from argv or env
    pw1 = getpass.getpass("Admin password (min 16 chars · won't echo): ")
    if len(pw1) < MIN_PASSWORD_LEN:
        raise SystemExit(
            f"[refuse] password too short · need at least {MIN_PASSWORD_LEN} chars · got {len(pw1)}."
        )
    pw2 = getpass.getpass("Confirm password: ")
    if pw1 != pw2:
        raise SystemExit("[refuse] passwords do not match.")
    return pw1


def main() -> int:
    print("─────────────────────────────────────────────────────────────")
    print("DefendableOS · platform_admin bootstrap")
    print("─────────────────────────────────────────────────────────────")
    print("This script creates the FIRST platform_admin user.")
    print("Password is read from /dev/tty without echo · never logged.")
    print("Use POST /api/v1/auth/login with this email + password to get a JWT.")
    print()

    email = _prompt_email()
    name = _prompt_name()
    pw = _prompt_password()

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            # Refuse · don't silently overwrite. Operator can promote
            # via direct SQL if needed but this script will not do it.
            raise SystemExit(
                f"[refuse] user with email {email} already exists · "
                f"cannot overwrite via this script. To promote that user "
                f"to platform_admin, update the row directly in psql:\n"
                f"  UPDATE users SET is_platform_admin = TRUE WHERE email = '{email}';"
            )
        user = User(
            email=email,
            name=name,
            hashed_password=hash_password(pw),
            is_platform_admin=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Defensive · purge password from local scope immediately
        del pw
        print()
        print(f"[OK] platform_admin user created · id={user.id} · email={user.email}")
        print()
        print("Next: POST /api/v1/auth/login with this email + password to get a JWT.")
        print("Then use that JWT as `Authorization: Bearer <jwt>` on /api/v1/claw-bakery/admin/* routes.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
