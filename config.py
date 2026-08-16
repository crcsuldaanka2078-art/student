import os


def _env(name, default):
    """Return the env var if set and non-empty, otherwise the default."""
    value = os.environ.get(name, "")
    return value if value.strip() else default


SUPABASE_URL = _env(
    "SUPABASE_URL",
    "https://guzaedkncejspqxcdsqm.supabase.co",
)

# Anon key (public key — safe to embed in the app).
SUPABASE_ANON_KEY = _env(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1emFlZGtuY2Vqc3BxeGNkc3FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY3NjAwMTgsImV4cCI6MjEwMjMzNjAxOH0.KxUpIJVfMYgD0nVP_TFUvT9R-bYkQWQ8bdP1x83-xAw",
)

SECRET_KEY = _env("SECRET_KEY", "change-me-in-production")