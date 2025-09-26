

from models.lab.lab import LabService, LabServiceGroupTag
from models.services.services import PriceCode, BusinessServices, ServiceType


def insert_lab_service(session, data):
    for test in data:
        # Insert into PriceCode
        price_entry = PriceCode(
            id=test["price_code"],
            service_price=test["service_price"],
            discount=test["discount_price"]
        )
        session.add(price_entry)
        session.flush()  # Get generated ID

        # Insert into BusinessServices
        service_entry = BusinessServices(
            # service_id=test["id"],
            price_code=test["price_code"],
            ext_turn_around_time=120,  # Default
            visibility="Active",  # Adjust based on your logic
            serviceType=ServiceType.Laboratory  # Adjust based on enum
        )
        session.add(service_entry)
        session.flush()

        # Insert into LabService
        lab_service_entry = LabService(
            id=test["id"],
            lab_id=1,
            lab_service_name=test["test_title"],
            lab_service_desc=test["lab_test_desc"],
            service_id=service_entry.service_id
        )
        session.add(lab_service_entry)

        lab_group_tag = LabServiceGroupTag(
            lab_service_group=1,  # Adjust based on group assignments
            lab_service_id=lab_service_entry.id
        )
        session.add(lab_group_tag)
        print("Processing Laboratory Service: ", test['test_title'])
    # Commit all changes
    session.commit()


print("Data successfully inserted into the database!")
