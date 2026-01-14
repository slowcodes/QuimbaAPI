from typing import List

from sqlalchemy.orm import Session

from dtos.all import DataResponseDTO
from dtos.lab import LabBundleCollectionDTO
from dtos.service_dtos.bundles import BundleDTO
from models.lab.lab import LabBundleCollection
from models.services.services import Bundles, ServiceType
from repos.lab.lab_repository import LabRepository


class ServiceBundleRepository:
    def __init__(self, session: Session):
        self.session = session
        self.lab_repository = LabRepository(session)

    def add_service_bundle(self, service_bundle: BundleDTO):
        sb = Bundles(**service_bundle.dict(exclude_unset=True))
        self.session.add(sb)
        self.session.commit()
        self.session.refresh(sb)
        return BundleDTO.from_orm(sb)  # coverts orm back to dto

    def update_bundle(self, service_bundle: BundleDTO):
        bdl = self.session.query(Bundles).filter(Bundles.id == service_bundle.id).first()
        bdl.bundles_name = service_bundle.bundles_name
        bdl.bundles_desc = service_bundle.bundles_desc
        bdl.discount = service_bundle.discount
        bdl.bundle_type = service_bundle.bundle_type

        bdl.lab_service_bundle.clear()
        for bundle_collection in service_bundle.lab_service_bundle:
            bdl.lab_service_bundle.append(
                LabBundleCollection(
                    lab_service_id=bundle_collection.lab_service_id
                )
            )
        self.session.commit()
        self.session.refresh(bdl)
        return bdl

    def get_all_bundles(
        self,
        limit: int = 20,
        skip: int = 0,
        service_type: ServiceType = None,
        keyword: str = None,
    ):
        bundles = self.session.query(Bundles)
        if keyword:
            bundles = bundles.filter(Bundles.bundles_name.ilike(f"%{keyword}%"))
        total = bundles.count()
        bundles = bundles.offset(skip).limit(limit).all()

        return {
            "data": [BundleDTO.from_orm(bundle) for bundle in bundles],
            "total": total
        }

    def add_lab_bundle(self, lab_bundle_item: LabBundleCollectionDTO):
        bundle = LabBundleCollection(
            bundles_id=lab_bundle_item.bundles_id,
            lab_service_id=lab_bundle_item.lab_service_id
        )
        self.session.add(bundle)
        self.session.commit()
        self.session.refresh(bundle)
        return bundle

    def delete_bundle(self, bundle_id) -> bool:
        bundle = self.session.query(Bundles).filter(Bundles.id == bundle_id).one()
        if bundle:
            bundle_collection = self.session.query(LabBundleCollection).filter(
                LabBundleCollection.bundles_id == bundle_id).all()

            for collection in bundle_collection:
                self.session.delete(collection)
                # self.session.commit()

            self.session.delete(bundle)
            self.session.commit()

            return True

        return False

    def get_service_bundle_services(self, bundle_id: int):
        bundle = self.session.query(Bundles).filter(Bundles.id == bundle_id).one()
        if bundle:
            bundle_services = self.session.query(LabBundleCollection).filter(
                LabBundleCollection.bundles_id == bundle_id).all()

            lab_services = []
            for service in bundle_services:
                lab_service = self.lab_repository.get_lab_service_details_by_service_id(service.lab_service_id)
                lab_services.append(lab_service)

            return lab_services

        return None

    def delete_lab_bundle(self, lab_collection_id: int):
        bundle = self.session.query(LabBundleCollection).filter(LabBundleCollection.id == lab_collection_id).first()
        if bundle:
            self.session.delete(bundle)
            self.session.commit()
            # self.session.refresh()
            return True
        return False
