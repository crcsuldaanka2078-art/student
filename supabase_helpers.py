"""Helpers for working with Supabase.

Used to:
  - Verify the connection.
  - Optionally bootstrap (create tables via SQL) the Supabase schema.

Requires the values in .env:
  SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, DATABASE_URL

Usage:
  python supabase_helpers.py test      # verify connection & print status
  python supabase_helpers.py bootstrap # create tables (if they do not exist)
"""
import os
import sys

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_client():
    """Return a Supabase client (REST) using the service role key."""
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and a SUPABASE key must be set in .env")
    return create_client(url, key)


def test_connection():
    print("Testing Supabase connection...")
    client = get_client()
    try:
        data = client.table("students").select("*").limit(1).execute()
        print(f"OK - connected to {os.environ.get('SUPABASE_URL')}")
        print("students table exists, sample row count check succeeded.")
        return True
    except Exception as exc:
        print(f"Connection OK but table check failed: {exc}")
        print("Run:  python supabase_helpers.py bootstrap")
        return True


def bootstrap():
    """Create the schema in Supabase using the SQLAlchemy models via the pooler."""
    from app import app

    with app.app_context():
        from models import db

        db.create_all()
        print("Bootstrap complete - tables created (if they did not already exist).")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "test"
    if action == "test":
        test_connection()
    elif action == "bootstrap":
        bootstrap()
    else:
        print("Unknown action. Use: test | bootstrap")