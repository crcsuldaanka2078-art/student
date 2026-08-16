import os

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://guzaedkncejspqxcdsqm.supabase.co",
)

# Anon key (public key — safe to embed in the app).
SUPABASE_ANON_KEY = os.environ.get(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1emFlZGtuY2Vqc3BxeGNkc3FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY3NjAwMTgsImV4cCI6MjEwMjMzNjAxOH0.KxUpIJVfMYgD0nVP_TFUvT9R-bYkQWQ8bdP1x83-xAw",
)

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")