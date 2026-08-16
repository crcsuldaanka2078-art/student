"""Seed the Supabase database with positions, candidates, eligible students
and student accounts.

Requires the tables to already exist (run supabase_schema.sql in the
Supabase SQL Editor first).

Usage:  python seed_supabase.py
"""
from werkzeug.security import generate_password_hash

from supabase_client import supabase

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

POSITIONS = [
    ("Madaxweyne (President)", "Hogaamiyaha ardayda ee dugsiga oo dhan."),
    ("Madaxweyne Ku-xigeen (Vice President)", "Caawiyaha madaxweynaha ardayda."),
    ("Xoghayaha Guud (Secretary)", "Mas'uulka qoraallada iyo diiwaanka."),
    ("Khasnajiga (Treasurer)", "Mas'uulka maaliyadda ururka ardayda."),
]

CANDIDATES = [
    ("Arday16", "Cabdiraxmaan Warsame", 1, "Waxaan rabaa horumar, waxbarasho sare iyo sinnaan arday oo dhan."),
    ("Arday17", "Hodan Cabdi", 1, "Naadi cusub oo ciyaaraha, fanka iyo horumarinta xirfadaha."),
    ("Arday18", "Maxamed Faarax", 1, "Arday walba codkiisa waa la dhegeystaa; wada-tashi horudhac ah."),
    ("Arday19", "Sahra Ibraahim", 2, "Taageera ardayda naafada ah iyo kulliyadda adag."),
    ("Arday20", "Yusuf Axmed", 2, "Kaalmo waxbarasho iyo tababaro xilli kasta."),
    ("Arday21", "Fartuun Cali", 3, "Waxtar, daah-furnaan iyo warbixin joogto ah oo loogu talagalay ardayda."),
    ("Arday22", "Saciid Cumar", 3, "Diiwaanka iyo xeerarka si nidaamsan u ilaaliya."),
    ("Arday23", "Ayaan Axmed", 4, "Maamul maaliyadeed oo daah-furan oo loogu talagalay mashaariicda ardayda."),
    ("Arday24", "Bilaal Maxamed", 4, "Kobcinta kheyraadka ururka iyo maal-gelinta mashaariicda."),
]


def clear_table(name):
    # Delete all rows (RLS allows anon delete in this demo schema).
    supabase.table(name).delete().gt("id", 0).execute()


def main():
    print("Seeding eligible_students...")
    clear_table("eligible_students")
    supabase.table("eligible_students").insert(
        [{"student_id": sid, "name": name, "email": email} for sid, name, email in STUDENTS]
    ).execute()

    print("Seeding students...")
    clear_table("students")
    supabase.table("students").insert(
        [
            {
                "student_id": sid,
                "name": name,
                "email": email,
                "password_hash": generate_password_hash("password123"),
            }
            for sid, name, email in STUDENTS
        ]
    ).execute()

    print("Seeding positions...")
    clear_table("positions")
    pos_rows = (
        supabase.table("positions")
        .insert([{"name": name, "description": desc} for name, desc in POSITIONS])
        .execute()
    )
    pos_by_index = {row["name"]: row["id"] for row in pos_rows.data}

    print("Seeding candidates...")
    clear_table("candidates")
    for sid, name, pos_index, manifesto in CANDIDATES:
        supabase.table("candidates").insert(
            {
                "student_id": sid,
                "name": name,
                "position_id": pos_by_index[POSITIONS[pos_index - 1][0]],
                "manifesto": manifesto,
            }
        ).execute()

    print("Clearing votes...")
    clear_table("votes")

    print("Done! Supabase is seeded.")
    print("-" * 50)
    print("Test login:")
    for sid, _, _ in STUDENTS:
        print(f"  Student ID: {sid}  |  Password: password123")


if __name__ == "__main__":
    main()