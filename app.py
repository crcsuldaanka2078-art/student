from datetime import datetime, timezone
from functools import wraps

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
        self.photo_url = row.get("photo_url") or ""


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
            "winner": total > 0 and counts.get(c["id"], 0) == max(counts.values()) if counts else False,
        }
        for c in candidates
    ]
    rows.sort(key=lambda r: r["votes"], reverse=True)
    return rows


def get_active_election():
    """Return the latest election row, auto-closing if its end time passed."""
    try:
        rows = supabase.table("elections").select("*").order("id").execute().data
    except Exception:
        return None
    if not rows:
        return None
    election = rows[-1]
    end_at = election.get("end_at")
    if election.get("is_open") and end_at:
        try:
            end = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > end:
                supabase.table("elections").update({"is_open": False}).eq("id", election["id"]).execute()
                election["is_open"] = False
        except (ValueError, TypeError):
            pass
    return election


def is_election_open():
    election = get_active_election()
    return bool(election and election.get("is_open"))


# ---------------- Admin auth (session-based) ----------------

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Admin kaliya ayaa geli kara boggan.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def fetch_admin(username):
    rows = (
        supabase.table("admins")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


# ---------------- Student routes ----------------

@login_manager.user_loader
def load_user(user_id):
    return fetch_student_by_pk(int(user_id))


@app.route("/")
def index():
    positions = fetch_positions()
    results = {}
    for pos in positions:
        results[pos.id] = get_position_results(pos.id)
    return render_template(
        "index.html",
        positions=positions,
        results=results,
        election=get_active_election(),
    )


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

    if not is_election_open():
        flash("Doorashadu waa xiran tahay ama well ma furmin. Waqtiga codbixinta la xannibay.", "error")
        return redirect(url_for("election_closed"))

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

        if not is_election_open():
            session.pop("pending_votes", None)
            flash("Doorashadu hadda waa xiran tahay, codka lama dhiibi karo.", "error")
            return redirect(url_for("election_closed"))

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


@app.route("/election-closed")
def election_closed():
    return render_template("election_closed.html", election=get_active_election())


@app.route("/results")
def results():
    positions = fetch_positions()
    data = {}
    for pos in positions:
        data[pos.id] = get_position_results(pos.id)
    return render_template(
        "results.html",
        positions=positions,
        data=data,
        election=get_active_election(),
    )


# ---------------- Admin routes ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = fetch_admin(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash(f"Ku soo dhawoow admin: {admin['username']}!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Username ama password khalad baa ah.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    flash("Admin ayaad ka baxday (logged out).", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "students": len(supabase.table("students").select("id").execute().data),
        "eligible": len(supabase.table("eligible_students").select("id").execute().data),
        "candidates": len(supabase.table("candidates").select("id").execute().data),
        "positions": len(supabase.table("positions").select("id").execute().data),
        "votes": len(supabase.table("votes").select("id").execute().data),
    }
    voters = {v["student_id"] for v in supabase.table("votes").select("student_id").execute().data}
    stats["voters"] = len(voters)
    stats["turnout"] = round(stats["voters"] / stats["eligible"] * 100, 1) if stats["eligible"] else 0.0
    return render_template("admin_dashboard.html", stats=stats, election=get_active_election())


# --- Students (admin) ---

@app.route("/admin/students")
@admin_required
def admin_students():
    students = supabase.table("students").select("id, student_id, name, email, created_at").order("id").execute().data
    return render_template("admin_students.html", students=students)


@app.route("/admin/students/add", methods=["GET", "POST"])
@admin_required
def admin_student_add():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not student_id or not name or not email or not password:
            flash("Dhammaan goobaha waa loo baahan yahay.", "error")
        elif len(password) < 4:
            flash("Password-ku waa in uu ka yaraa 4 xarfo.", "error")
        else:
            exists = supabase.table("students").select("id").or_(f"student_id.eq.{student_id},email.eq.{email}").limit(1).execute().data
            if exists:
                flash("Student ID ama email-kan horay ayaa loo diiwaangeliyay.", "error")
            else:
                supabase.table("students").insert(
                    {
                        "student_id": student_id,
                        "name": name,
                        "email": email,
                        "password_hash": generate_password_hash(password),
                    }
                ).execute()
                # Also make them eligible so they can be verified.
                elig = supabase.table("eligible_students").select("id").eq("student_id", student_id).limit(1).execute().data
                if not elig:
                    supabase.table("eligible_students").insert(
                        {"student_id": student_id, "name": name, "email": email}
                    ).execute()
                flash("Arday si guul leh ayaa loo diiwaangeliyay!", "success")
                return redirect(url_for("admin_students"))

    return render_template("admin_student_form.html", student=None)


@app.route("/admin/students/<int:sid>/edit", methods=["GET", "POST"])
@admin_required
def admin_student_edit(sid):
    rows = supabase.table("students").select("*").eq("id", sid).limit(1).execute().data
    if not rows:
        flash("Ardaykan lama helin.", "error")
        return redirect(url_for("admin_students"))
    student = rows[0]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        updates = {"name": name, "email": email}
        if password:
            updates["password_hash"] = generate_password_hash(password)
        supabase.table("students").update(updates).eq("id", sid).execute()
        flash("Waxaa la beddelay ardayga!", "success")
        return redirect(url_for("admin_students"))

    return render_template("admin_student_form.html", student=student)


@app.route("/admin/students/<int:sid>/delete", methods=["POST"])
@admin_required
def admin_student_delete(sid):
    supabase.table("students").delete().eq("id", sid).execute()
    flash("Ardayga waa la tirtiray.", "success")
    return redirect(url_for("admin_students"))


# --- Candidates (admin) ---

@app.route("/admin/candidates")
@admin_required
def admin_candidates():
    positions = fetch_positions()
    return render_template("admin_candidates.html", positions=positions)


@app.route("/admin/candidates/add", methods=["GET", "POST"])
@admin_required
def admin_candidate_add():
    positions = supabase.table("positions").select("*").order("id").execute().data
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        position_id = request.form.get("position_id", "").strip()
        manifesto = request.form.get("manifesto", "").strip()
        photo_url = request.form.get("photo_url", "").strip()
        student_id = request.form.get("student_id", "").strip()

        if not name or not position_id:
            flash("Magaca iyo xilku waa loo baahan yahay.", "error")
        else:
            supabase.table("candidates").insert(
                {
                    "name": name,
                    "position_id": int(position_id),
                    "manifesto": manifesto,
                    "photo_url": photo_url,
                    "student_id": student_id,
                }
            ).execute()
            flash("Musharrax si guul leh ayaa loo daray!", "success")
            return redirect(url_for("admin_candidates"))

    return render_template("admin_candidate_form.html", candidate=None, positions=positions)


@app.route("/admin/candidates/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def admin_candidate_edit(cid):
    rows = supabase.table("candidates").select("*").eq("id", cid).limit(1).execute().data
    if not rows:
        flash("Musharraxkan lama helin.", "error")
        return redirect(url_for("admin_candidates"))
    candidate = rows[0]
    positions = supabase.table("positions").select("*").order("id").execute().data

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        position_id = request.form.get("position_id", "").strip()
        manifesto = request.form.get("manifesto", "").strip()
        photo_url = request.form.get("photo_url", "").strip()
        student_id = request.form.get("student_id", "").strip()

        supabase.table("candidates").update(
            {
                "name": name,
                "position_id": int(position_id),
                "manifesto": manifesto,
                "photo_url": photo_url,
                "student_id": student_id,
            }
        ).eq("id", cid).execute()
        flash("Musharraxka waa la beddelay!", "success")
        return redirect(url_for("admin_candidates"))

    return render_template("admin_candidate_form.html", candidate=candidate, positions=positions)


@app.route("/admin/candidates/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_candidate_delete(cid):
    supabase.table("candidates").delete().eq("id", cid).execute()
    flash("Musharraxka waa la tirtiray.", "success")
    return redirect(url_for("admin_candidates"))


# --- Positions (admin) ---

@app.route("/admin/positions")
@admin_required
def admin_positions():
    positions = supabase.table("positions").select("*").order("id").execute().data
    return render_template("admin_positions.html", positions=positions)


@app.route("/admin/positions/add", methods=["GET", "POST"])
@admin_required
def admin_position_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if not name:
            flash("Magaca xilka waa loo baahan yahay.", "error")
        else:
            supabase.table("positions").insert({"name": name, "description": description}).execute()
            flash("Xil si guul leh ayaa loo daray!", "success")
            return redirect(url_for("admin_positions"))
    return render_template("admin_position_form.html", position=None)


@app.route("/admin/positions/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_position_edit(pid):
    rows = supabase.table("positions").select("*").eq("id", pid).limit(1).execute().data
    if not rows:
        flash("Xilkan lama helin.", "error")
        return redirect(url_for("admin_positions"))
    position = rows[0]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        supabase.table("positions").update({"name": name, "description": description}).eq("id", pid).execute()
        flash("Xilka waa la beddelay!", "success")
        return redirect(url_for("admin_positions"))

    return render_template("admin_position_form.html", position=position)


@app.route("/admin/positions/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_position_delete(pid):
    supabase.table("positions").delete().eq("id", pid).execute()
    flash("Xilka waa la tirtiray.", "success")
    return redirect(url_for("admin_positions"))


# --- Elections (admin) ---

@app.route("/admin/elections")
@admin_required
def admin_elections():
    elections = supabase.table("elections").select("*").order("id").execute().data
    return render_template("admin_elections.html", elections=elections)


@app.route("/admin/elections/add", methods=["GET", "POST"])
@admin_required
def admin_election_add():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        start_at = request.form.get("start_at", "").strip()
        end_at = request.form.get("end_at", "").strip()
        is_open = request.form.get("is_open") == "on"

        if not title:
            flash("Cinwaanka doorashada waa loo baahan yahay.", "error")
        else:
            payload = {"title": title, "is_open": is_open}
            if start_at:
                payload["start_at"] = start_at
            if end_at:
                payload["end_at"] = end_at
            supabase.table("elections").insert(payload).execute()
            flash("Doorasho si guul leh ayaa loo sameeyay!", "success")
            return redirect(url_for("admin_elections"))
    return render_template("admin_election_form.html", election=None)


@app.route("/admin/elections/<int:eid>/edit", methods=["GET", "POST"])
@admin_required
def admin_election_edit(eid):
    rows = supabase.table("elections").select("*").eq("id", eid).limit(1).execute().data
    if not rows:
        flash("Doorashadan lama helin.", "error")
        return redirect(url_for("admin_elections"))
    election = rows[0]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        start_at = request.form.get("start_at", "").strip()
        end_at = request.form.get("end_at", "").strip()
        is_open = request.form.get("is_open") == "on"

        payload = {"title": title, "is_open": is_open}
        if start_at:
            payload["start_at"] = start_at
        else:
            payload["start_at"] = None
        if end_at:
            payload["end_at"] = end_at
        else:
            payload["end_at"] = None
        supabase.table("elections").update(payload).eq("id", eid).execute()
        flash("Doorashada waa la beddelay!", "success")
        return redirect(url_for("admin_elections"))

    return render_template("admin_election_form.html", election=election)


@app.route("/admin/elections/<int:eid>/toggle", methods=["POST"])
@admin_required
def admin_election_toggle(eid):
    rows = supabase.table("elections").select("*").eq("id", eid).limit(1).execute().data
    if rows:
        new_state = not rows[0].get("is_open", False)
        supabase.table("elections").update({"is_open": new_state}).eq("id", eid).execute()
        flash("Doorashada waa la furay" if new_state else "Doorashada waa la xiray.", "success")
    return redirect(url_for("admin_elections"))


@app.route("/admin/elections/<int:eid>/delete", methods=["POST"])
@admin_required
def admin_election_delete(eid):
    supabase.table("elections").delete().eq("id", eid).execute()
    flash("Doorashada waa la tirtiray.", "success")
    return redirect(url_for("admin_elections"))


# --- Votes (admin view) ---

@app.route("/admin/votes")
@admin_required
def admin_votes():
    positions = fetch_positions()
    data = {}
    for pos in positions:
        data[pos.id] = get_position_results(pos.id)
    return render_template("admin_votes.html", positions=positions, data=data)


# --- Reports (admin) ---

@app.route("/admin/reports")
@admin_required
def admin_reports():
    students = len(supabase.table("students").select("id").execute().data)
    eligible = len(supabase.table("eligible_students").select("id").execute().data)
    total_votes = len(supabase.table("votes").select("id").execute().data)
    voters = {v["student_id"] for v in supabase.table("votes").select("student_id").execute().data}
    total_voters = len(voters)
    turnout = round(total_voters / eligible * 100, 1) if eligible else 0.0

    positions = fetch_positions()
    results = {}
    for pos in positions:
        results[pos.id] = get_position_results(pos.id)

    return render_template(
        "admin_reports.html",
        students=students,
        eligible=eligible,
        total_votes=total_votes,
        total_voters=total_voters,
        turnout=turnout,
        positions=positions,
        results=results,
    )


if __name__ == "__main__":
    app.run(debug=True)