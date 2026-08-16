# Nidaamka Codbixinta Ardayda (Student Voting System)

Student election voting system built with **Flask** (backend) and **Tailwind CSS** (frontend).

## Features

- 🧑‍🎓 **Student Registration / Login** — create an account with Student ID + password, log in / log out. Passwords are securely hashed. Student ID & email must be unique. **Only students listed in the official `EligibleStudent` registry (matching Student ID + name) can register** — anyone else is rejected, verifying they are a real student.
- 🗳️ **Voting** — a logged-in student can see all candidates per position and select **one candidate per position**. There is a **confirmation step** before the ballot is submitted. **A student may vote only once, and once submitted the vote is final and cannot be changed.**
- 📊 **Results** — live tally and percentage bars per position.

## Project Structure

```
student-voting/
├── app.py                 # Flask routes + logic
├── models.py              # Database models (EligibleStudent, Student, Position, Candidate, Vote)
├── seed.py                # Seeds sample data + test accounts
├── requirements.txt
├── templates/             # Jinja2 HTML templates
├── static/css/
│   ├── output.css         # Compiled CSS (ready to use, no build needed)
│   └── input.css          # Tailwind source (optional, for rebuilding)
├── tailwind.config.js
└── package.json           # Optional: Tailwind build scripts
```

## Setup & Run

### 1. Install Python (if not installed)

Download from https://www.python.org/downloads/ (check "Add Python to PATH").

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed the database (creates voting.db with sample data)

```bash
python seed.py
```

This prints test login accounts, for example:

```
Student ID: STU001  |  Password: password123
```

### 4. Run the app

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Test Accounts (from seed)

| Student ID | Password |
|------------|----------|
| STU001     | password123 |
| STU002     | password123 |
| STU003     | password123 |
| STU004     | password123 |
| STU005     | password123 |

## Rebuilding Tailwind CSS (optional)

The `static/css/output.css` file is ready to use. If you edit templates and want to regenerate the CSS:

```bash
npm install
npm run css          # one-time build
npm run css:watch    # rebuild on change
```

## Deploying on Render.com (gunicorn)

This app uses **Supabase** for the database, so no local database is needed.

### Setup Supabase tables (once)
1. Create a Supabase project at https://supabase.com
2. Open **SQL Editor** → **New query**
3. Paste the contents of `supabase_schema.sql` and run it
4. Run `python populate_supabase.py` (or `python seed_supabase.py` for full seed incl. accounts)

### Deploy
1. Push this repo to GitHub
2. On Render.com → **New → Web Service** → connect your GitHub repo
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Add environment variables in Render dashboard:
   - `SUPABASE_URL` — your Supabase project URL
   - `SUPABASE_ANON_KEY` — your Supabase anon key
   - `SECRET_KEY` — any random long string
5. Deploy. The service runs with `gunicorn app:app` (see `Procfile`).

> A `render.yaml` is also included for Blueprint deploys.

## Security Notes

- Passwords are stored as salted hashes (Werkzeug `generate_password_hash`).
- Uses Flask-Login for session management and `@login_required` guards on voting.
- For production set `SECRET_KEY` via env var (never commit real secrets).
- The Supabase anon key is safe to embed (public key); never embed the service_role key.
- Registration verifies the Student ID + name against the `EligibleStudent` registry, so only genuine students can create an account.
- Votes are one-time and immutable: after confirmation a student cannot re-vote or change their ballot (enforced both in the UI and server-side via the `has_voted` guard and the unique `(student_id, position_id)` constraint).
