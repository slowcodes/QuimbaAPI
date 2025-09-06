import datetime

from models.client import Person, Sex, Client, MaritalStatus


def insert_patients(session, patients):
    for patient in patients:
        person = Person(
            first_name=patient["first_name"],
            last_name=patient["last_name"],
            sex=Sex(patient["sex"]),
            email=patient["email"] if patient["email"] else None,
            phone=patient["phone"],
            enrollment_date=datetime.datetime.strptime(patient["reg_day"], "%Y-%m-%d %H:%M:%S")
        )
        session.add(person)
        session.flush()  # Get person ID before committing
        client = Client(
            person_id=person.id,
            lga_id=1,
            occupation_id=1,
            marital_status=MaritalStatus(patient["marrital_status"]),
            date_of_birth=datetime.datetime.strptime(patient["dob"], "%Y-%m-%d").date(),
            address=patient["address"] if patient["address"] else None
        )
        session.add(client)
        print("Processing Patient: ", patient["first_name"], patient["last_name"], "-", patient["patient_id"])
    session.commit()
