from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
    UserMixin,
)
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter

from supabase_client import supabase
from config import SECRET_KEY

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Fadlan ku soo gal (login) si aad ugu codeyso."
login_manager.login_message_category = "error"


# ---------------- Data wrappers (Supabase rows -> objects) ----------------

class Vote:
    def __init__(self, row):
        self.id = row["id"]
        self.student_id = row["student_id"]
        self.position_id = row["position_id"]
        self.candidate_id = row["candidate_id"]


class Candidate:
    def __init__(self, row):
        self.id = row["id"]
        self.position_id = row["position_id"]
        self.name = row["name"]
        self.student_id = row.get("student_id")
        self.manifesto = row.get("manifesto") or ""
        self.photo_url = row.get("photo_url")


class Position:
    def __init__(self, row):
        self.id = row["id"]
        self.name = row["name"]
        self.description = row.get("description") or ""
        self.candidates = [Candidate(c) for c in row.get("candidates", [])]


class Student(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.student_id = row["student_id"]
        self.name = row["name"]
        self.email = row["email"]
        self.password_hash = row["password_hash"]
        self.votes = [Vote(v) for v in row.get("votes", [])]

    @property
    def has_voted(self):
        return len(self.votes) > 0

    def get_id(self):
        return str(self.id)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------- Helpers ----------------

def fetch_student_row(student_id):
    """Return the students row (with votes) for a student_id, or None."""
    rows = supabase.table("students").select("*").eq("student_id", student_id).limit(1).execute().data
    if not rows:
        return None
    return attach_votes(rows[0])


def fetch_student_by_pk(uid):
    rows = supabase.table("students").select("*").eq("id", uid).limit(1).execute().data
    if not rows:
        return None
    return attach_votes(rows[0])


def attach_votes(student_row):
    votes = supabase.table("votes").select("*").eq("student_id", student_row["id"]).execute().data
    student_row["votes"] = votes
    return Student(student_row)


def fetch_positions():
    rows = supabase.table("positions").select("*").order("id").execute().data
    positions = []
    for row in rows:
        cands = (
            supabase.table("candidates")
            .select("*")
            .eq("position_id", row["id"])
            .order("id")
            .execute()
            .data
        )
        positions.append(Position({**row, "candidates": cands}))
    return positions


def fetch_candidate(candidate_id):
    rows = (
        supabase.table("candidates")
        .select("*")
        .eq("id", candidate_id)
        .limit(1)
        .execute()
        .data
    )
    return Candidate(rows[0]) if rows else None


def get_position_results(position_id):
    candidates = (
        supabase.table("candidates")
        .select("id, name")
        .eq("position_id", position_id)
        .execute()
        .data
    )
    votes = supabase.table("votes").select("candidate_id").eq("position_id", position_id).execute().data
    counts = Counter(v["candidate_id"] for v in votes)
    total = len(votes)
    rows = [
        {
            "name": c["name"],
            "votes": counts.get(c["id"], 0),
            "pct": round(counts.get(c["id"], 0) / total * 100, 1) if total else 0.0,
        }
        for c in candidates
    ]
    rows.sort(key=lambda r: r["votes"], reverse=True)
    return rows


# ---------------- Routes ----------------

@login_manager.user_loader
def load_user(user_id):
    return fetch_student_by_pk(int(user_id))


@app.route("/")
def index():
    positions = fetch_positions()
    results = {}
    for pos in positions:
        results[pos.id] = get_position_results(pos.id)
    return render_template("index.html", positions=positions, results=results)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("vote"))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = validate_registration(student_id, name, email, password, confirm)
        if error:
            flash(error, "error")
            return render_template("register.html", form=request.form)

        supabase.table("students").insert(
            {
                "student_id": student_id,
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password),
            }
        ).execute()

        flash("Xisaabtaada si guul leh ayaa loo sameeyay. Hadda ku soo gal!", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form={})


def validate_registration(student_id, name, email, password, confirm):
    if not student_id or not name or not email or not password:
        return "Dhammaan goobaha waa loo baahan yahay."
    if password != confirm:
        return "Lambarka sirta (password) isma la mid aha."
    if len(password) < 4:
        return "Password-ku waa in uu ka yaraa 4 xarfo."

    existing = (
        supabase.table("students")
        .select("id")
        .or_(f"student_id.eq.{student_id},email.eq.{email}")
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return "Student ID ama email-kan horay ayaa loo diiwaangeliyay."

    eligible = (
        supabase.table("eligible_students")
        .select("student_id, name")
        .eq("student_id", student_id)
        .limit(1)
        .execute()
        .data
    )
    if not eligible:
        return "Student ID-kan ma aha student sax ah oo diiwaangelisan. La xiriir maamulka."
    if eligible[0]["name"].strip().lower() != name.strip().lower():
        return "Magaca (name) kuma habboona Student ID-ga. Hubi inaad gashay magaca saxda ah."
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("vote"))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        student = fetch_student_row(student_id)
        if student and student.check_password(password):
            login_user(student)
            flash(f"Ku soo dhawoow, {student.name}!", "success")
            return redirect(url_for("vote"))

        flash("Student ID ama password khalad baa ah. Fadlan mar kale isku day.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Waa kuu guuleysatay (logged out).", "success")
    return redirect(url_for("login"))


@app.route("/vote", methods=["GET", "POST"])
@login_required
def vote():
    if current_user.has_voted:
        return render_template("voted.html", positions=fetch_positions())

    positions = fetch_positions()
    existing = {v.position_id: v.candidate_id for v in current_user.votes}

    if request.method == "POST":
        submitted = collect_submitted(request.form)
        if not submitted:
            flash("Fadlan u codee ugu yaraan hal xil (position).", "error")
            return redirect(url_for("vote"))

        session["pending_votes"] = submitted
        return redirect(url_for("vote_confirm"))

    return render_template("vote.html", positions=positions, existing=existing)


def collect_submitted(form):
    submitted = []
    for key, candidate_id in form.items():
        if key.startswith("position_") and candidate_id.isdigit():
            position_id = int(key.split("_")[1])
            candidate = fetch_candidate(int(candidate_id))
            if candidate and candidate.position_id == position_id:
                submitted.append((position_id, int(candidate_id)))
    return submitted


@app.route("/vote/confirm", methods=["GET", "POST"])
@login_required
def vote_confirm():
    if current_user.has_voted:
        session.pop("pending_votes", None)
        return render_template("voted.html", positions=fetch_positions())

    pending = session.get("pending_votes")
    if not pending:
        return redirect(url_for("vote"))

    if request.method == "POST":
        # A student may only ever vote once. Guard against double submission.
        if current_user.has_voted:
            session.pop("pending_votes", None)
            flash("Codkaga horay ayaa loo dhiibay. Hal mar kaliya ayaad cod bixin kartaa.", "error")
            return redirect(url_for("vote"))

        rows = []
        for position_id, candidate_id in pending:
            candidate = fetch_candidate(candidate_id)
            if candidate and candidate.position_id == position_id:
                rows.append(
                    {
                        "student_id": current_user.id,
                        "position_id": position_id,
                        "candidate_id": candidate_id,
                    }
                )
        if rows:
            supabase.table("votes").insert(rows).execute()

        session.pop("pending_votes", None)
        flash("Codkaga si guul leh ayaa loo dhiibay (voted)! Mahadsanid.", "success")
        return redirect(url_for("voted"))

    summary = []
    positions = {p.id: p for p in fetch_positions()}
    for position_id, candidate_id in pending:
        candidate = fetch_candidate(candidate_id)
        summary.append(
            {
                "position": positions.get(position_id).name if positions.get(position_id) else "?",
                "candidate": candidate.name if candidate else "?",
                "position_id": position_id,
                "candidate_id": candidate_id,
            }
        )

    return render_template("confirm.html", summary=summary)


@app.route("/voted")
@login_required
def voted():
    return render_template("voted.html", positions=fetch_positions())


@app.route("/results")
def results():
    positions = fetch_positions()
    data = {}
    for pos in positions:
        data[pos.id] = get_position_results(pos.id)
    return render_template("results.html", positions=positions, data=data)


if __name__ == "__main__":
    app.run(debug=True)