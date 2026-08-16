"""Populate eligible_students, positions, candidates, admins and elections.

Requires the tables to already exist (run supabase_schema.sql in the
Supabase SQL Editor first).

Usage:  python populate_supabase.py
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
    ("Xiriirka Bulshada (Public Relations)", "Mas'uulka xiriirka ardayda iyo warbaahinta."),
    ("Arrimaha Tacliinta (Academic Affairs)", "Mas'uulka horumarinta waxbarashada iyo tacliinta."),
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
    # Public Relations
    ("Arday25", "Khadar Jaamac", 5, "Kordhinta ardayda cusub iyo saaxiibtinimada xooggan."),
    ("Arday26", "Munira Axmed", 5, "Warbaahinta iyo wacyigelinta ardayda oo dhan."),
    # Academic Affairs
    ("Arday27", "Ciise Cabdullahi", 6, "Kaalmooyin waxbarasho, maktabadda iyo kooxaha tacliinta."),
    ("Arday28", "Hamda Nuur", 6, "Horumarinta barnaamijyada waxbarashada iyo xirfadaha."),
]


def clear_table(name):
    supabase.table(name).delete().gt("id", 0).execute()


def main():
    print("Populating eligible_students (15) ...")
    clear_table("eligible_students")
    supabase.table("eligible_students").insert(
        [{"student_id": sid, "name": name, "email": email} for sid, name, email in STUDENTS]
    ).execute()

    print("Populating positions (6) ...")
    clear_table("positions")
    pos_rows = (
        supabase.table("positions")
        .insert([{"name": name, "description": desc} for name, desc in POSITIONS])
        .execute()
    )
    pos_by_index = {row["name"]: row["id"] for row in pos_rows.data}

    print("Populating candidates (13) ...")
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

    print("Populating admin ...")
    clear_table("admins")
    supabase.table("admins").insert(
        {
            "username": "admin",
            "password_hash": generate_password_hash("admin123"),
        }
    ).execute()

    print("Clearing elections ...")
    clear_table("elections")

    print("Done! Now students can register from the registration page.")
    print("-" * 50)
    print("Admin login:")
    print("  Username: admin  |  Password: admin123")
    print("-" * 50)
    print("Eligible students (can register):")
    for sid, name, _ in STUDENTS:
        print(f"  {sid} | {name}")


if __name__ == "__main__":
    main()