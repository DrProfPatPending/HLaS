#!/bin/bash
#

echo "Move to build directory..."
cd /opt/hlas
echo "Updating admin user passwords after import..."

echo "Running Python script to update users..."
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T backend python - <<'PY'
import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

# username/email -> new plain password
resets = {
    "rob@scoffin.com": "CTC2026!",
    "neil-gregory@btconnect.com": "CTC2026!",
    "richardbowes@hotmail.com": "CTC2026!",
    "john.s.gandy@gmail.com": "CTC2026!",
}

engine = create_engine(os.environ["DATABASE_URL"], future=True)

updated = 0
missing = []

with engine.begin() as conn:
    for user, plain_password in resets.items():
        pw_hash = generate_password_hash(plain_password)
        result = conn.execute(
            text("""
                UPDATE app_users
                SET username = :u,
                    email = COALESCE(NULLIF(email, ''), :u),
                    password_hash = :h,
                    is_active = TRUE,
                    updated_at = NOW()
                WHERE lower(username) = lower(:u)
                   OR lower(email) = lower(:u)
            """),
            {"u": user, "h": pw_hash},
        )
        if result.rowcount and result.rowcount > 0:
            updated += result.rowcount
            print(f"UPDATED: {user} ({result.rowcount} row)")
        else:
            missing.append(user)
            print(f"MISSING: {user}")

print(f"\nDone. Total updated rows: {updated}")
if missing:
    print("Not found:", ", ".join(missing))
PY

echo "Done..."
