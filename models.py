from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class EligibleStudent(db.Model):
    """The official registry of real students who may register and vote.

    Used to verify that a person registering is a genuine student. Only
    students whose ID and name appear here may create an account.
    """
    __tablename__ = "eligible_students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))

    def __repr__(self):
        return f"<EligibleStudent {self.student_id} {self.name}>"


class Student(UserMixin, db.Model):
    """An eligible voter: a registered student."""
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # A student may vote only once overall; each vote is final.
    votes = db.relationship("Vote", back_populates="student")

    @property
    def has_voted(self):
        return self.votes and len(self.votes) > 0

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Position(db.Model):
    """An elected role, e.g. 'President', 'Vice President'."""
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(300))

    candidates = db.relationship("Candidate", back_populates="position")


class Candidate(db.Model):
    """A student running for a position."""
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    student_id = db.Column(db.String(50))
    manifesto = db.Column(db.String(500))
    photo_url = db.Column(db.String(300))

    position = db.relationship("Position", back_populates="candidates")
    votes = db.relationship("Vote", back_populates="candidate")


class Vote(db.Model):
    """One student's choice for a single position."""
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="votes")
    position = db.relationship("Position")
    candidate = db.relationship("Candidate", back_populates="votes")

    __table_args__ = (
        db.UniqueConstraint("student_id", "position_id", name="uq_student_position"),
    )
