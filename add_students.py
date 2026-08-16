"""Add 10 more student accounts (Arday6-Arday15) to bring the total to 15.

Usage:  python add_students.py
"""
from app import app
from models import db, Student

EXTRA_STUDENTS = [
    ("Arday6", "Faadumo Xaashi", "faadumo@gmail.com"),
    ("Arday7", "Calasow Maxamed", "calasow@gmail.com"),
    ("Arday8", "Naima Cabdulle", "naima@gmail.com"),
    ("Arday9", "Jaamac Ciise", "jaamac@gmail.com"),
    ("Arday10", "Suhayb Cali", "suhayb@gmail.com"),
    ("Arday11", "Ubax Axmed", "ubax@gmail.com"),
    ("Arday12", "Kamar Nuur", "kamar@gmail.com"),
    ("Arday13", "Guuleed Warsame", "guuleed@gmail.com"),
    ("Arday14", "Ruwayda Cali", "ruwayda@gmail.com"),
    ("Arday15", "Mohamed Aadan", "mohamed@gmail.com"),
]


def main():
    with app.app_context():
        added = 0
        for sid, name, email in EXTRA_STUDENTS:
            if Student.query.filter_by(student_id=sid).first():
                print(f"Skip {sid}: already exists.")
                continue
            if Student.query.filter_by(email=email).first():
                print(f"Skip {sid}: email already exists.")
                continue
            s = Student(student_id=sid, name=name, email=email)
            s.set_password("password123")
            db.session.add(s)
            added += 1
        db.session.commit()
        print(f"Added {added} new students.")
        print("-" * 50)
        for s in Student.query.order_by(Student.id).all():
            print(f"{s.student_id} | {s.name} | {s.email} | password123")


if __name__ == "__main__":
    main()