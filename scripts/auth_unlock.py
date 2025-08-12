#!/usr/bin/env python3
"""
Unlock a Kari auth account by clearing Redis lockout counters and resetting DB flags.

Usage:
  python scripts/auth_unlock.py admin@kari.ai
  # or
  EMAIL=admin@kari.ai python scripts/auth_unlock.py
"""

import os
import sys
import argparse
import redis
import psycopg2
from psycopg2.extras import DictCursor

def main():
    parser = argparse.ArgumentParser(description="Unlock a Kari account (clear lockouts).")
    parser.add_argument("email", nargs="?", default=os.getenv("EMAIL"),
                        help="Email of the account to unlock (or set EMAIL env var)")
    parser.add_argument("--redis-url", default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                        help="Redis URL (default: env REDIS_URL or redis://localhost:6379/0)")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"),
                        help="Postgres DATABASE_URL (e.g. postgresql://user:pass@host:5432/db)")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without executing")
    args = parser.parse_args()

    if not args.email:
        print("ERROR: email is required (pass as arg or set EMAIL env var).", file=sys.stderr)
        sys.exit(2)

    if not args.database_url:
        print("ERROR: DATABASE_URL is required (set env or pass --database-url).", file=sys.stderr)
        sys.exit(2)

    email = args.email.strip().lower()
    lock_keys = [f"auth:lockout:{email}", f"auth:failcount:{email}"]

    print(f"[info] Target email: {email}")
    print(f"[info] Redis URL: {args.redis_url}")
    print(f"[info] DATABASE_URL: {args.database_url.split('@')[0]}@…")  # hide host/pass

    # --- Redis: delete lock keys ---
    try:
        r = redis.from_url(args.redis_url)
        if args.dry_run:
            print(f"[dry-run] Would delete Redis keys: {lock_keys}")
        else:
            deleted = sum(r.delete(k) for k in lock_keys)
            print(f"[ok] Redis cleared ({deleted} keys removed).")
    except Exception as e:
        print(f"[warn] Redis step failed: {e}", file=sys.stderr)

    # --- Postgres: reset flags in auth_users ---
    sql = """
        UPDATE auth_users
           SET is_locked = FALSE,
               failed_attempts = 0,
               locked_until = NULL
         WHERE email = %s
        RETURNING id, email, is_locked, failed_attempts, locked_until;
    """
    try:
        if args.dry_run:
            print(f"[dry-run] Would run SQL:\n{sql.strip()}\nwith email={email}")
        else:
            conn = psycopg2.connect(args.database_url)
            conn.autocommit = False
            try:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(sql, (email,))
                    row = cur.fetchone()
                conn.commit()
            finally:
                conn.close()

            if row:
                print(f"[ok] Unlocked {row['email']}; is_locked={row['is_locked']}, "
                      f"failed_attempts={row['failed_attempts']}, locked_until={row['locked_until']}")
            else:
                print(f"[warn] No user found for email: {email}")
    except Exception as e:
        print(f"[error] Postgres step failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("[done] Account unlock workflow complete.")

if __name__ == "__main__":
    main()
