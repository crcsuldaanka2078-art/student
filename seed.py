"""Seed the database with sample students, positions and candidates.

Usage:  python seed.py
"""
from app import app
from models import db, Student, Position, Candidate, EligibleStudent

STUDENTS = [
    ("Arday1", "Aamina Maxamed", "aamina@gmail.com"),
    ("Arday2", "Cabdullahi Cali", "cabdullahi@gmail.com"),
    ("Arday3", "Maryan Cismaan", "maryan@gmail.com"),
    ("Arday4", "Xasan Xuseen", "xasan@gmail.com"),
    ("Arday5", "Khadra Aadan", "khadra@gmail.com"),
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

# Official registry of real students. Only these may register and vote.
ELIGIBLE = STUDENTS[:]

POSITIONS = [
    ("Madaxweyne (President)", "Hogaamiyaha ardayda ee dugsiga oo dhan."),
    ("Madaxweyne Ku-xigeen (Vice President)", "Caawiyaha madaxweynaha ardayda."),
    ("Xoghayaha Guud (Secretary)", "Mas'uulka qoraallada iyo diiwaanka."),
    ("Khasnajiga (Treasurer)", "Mas'uulka maaliyadda ururka ardayda."),
]

CANDIDATES = [
    # President
    ("Arday16", "Cabdiraxmaan Warsame", 1, "Waxaan rabaa horumar, waxbarasho sare iyo sinnaan arday oo dhan."),
    ("Arday17", "Hodan Cabdi", 1, "Naadi cusub oo ciyaaraha, fanka iyo horumarinta xirfadaha."),
    ("Arday18", "Maxamed Faarax", 1, "Arday walba codkiisa waa la dhegeystaa; wada-tashi horudhac ah."),
    # Vice President
    ("Arday19", "Sahra Ibraahim", 2, "Taageera ardayda naafada ah iyo kulliyadda adag."),
    ("Arday20", "Yusuf Axmed", 2, "Kaalmo waxbarasho iyo tababaro xilli kasta."),
    # Secretary
    ("Arday21", "Fartuun Cali", 3, "Waxtar, daah-furnaan iyo warbixin joogto ah oo loogu talagalay ardayda."),
    ("Arday22", "Saciid Cumar", 3, "Diiwaanka iyo xeerarka si nidaamsan u ilaaliya."),
    # Treasurer
    ("Arday23", "Ayaan Axmed", 4, "Maamul maaliyadeed oo daah-furan oo loogu talagalay mashaariicda ardayda."),
    ("Arday24", "Bilaal Maxamed", 4, "Kobcinta kheyraadka ururka iyo maal-gelinta mashaariicda."),
]


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        for sid, name, email in ELIGIBLE:
            db.session.add(EligibleStudent(student_id=sid, name=name, email=email))

        for sid, name, email in STUDENTS:
            s = Student(student_id=sid, name=name, email=email)
            s.set_password("password123")
            db.session.add(s)

        for name, desc in POSITIONS:
            db.session.add(Position(name=name, description=desc))
        db.session.flush()

        positions = {p.name: p for p in Position.query.all()}

        for sid, name, pos_id, manifesto in CANDIDATES:
            pos = Position.query.filter_by(id=pos_id).first()
            db.session.add(
                Candidate(
                    student_id=sid,
                    name=name,
                    position_id=pos.id,
                    manifesto=manifesto,
                )
            )

        db.session.commit()

        print("Database seeded successfully!")
        print("-" * 50)
        print("Test login:")
        for sid, name, _ in STUDENTS:
            print(f"  Student ID: {sid}  |  Password: password123")
        print("-" * 50)
        print(f"Candidates: {len(CANDIDATES)}  |  Positions: {len(POSITIONS)}")
        print(f"Eligible students: {len(ELIGIBLE)}  |  Test accounts: {len(STUDENTS)}")


if __name__ == "__main__":
    seed()