from typing import List

from sqlalchemy.orm import Session

from commands.lab import LabBundleCollectionDTO
from commands.services import ServiceBundleDTO
from models.lab.lab import LabBundleCollection, LabService
from models.services import Bundles, ServiceType


class ServiceBundleRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_service_bundle(self, service_bundle: ServiceBundleDTO):
        sb = Bundles(**service_bundle.dict(exclude_unset=True))
        self.session.add(sb)
        self.session.commit()
        self.session.refresh(sb)
        return ServiceBundleDTO.from_orm(sb)  # coverts orm back to dto

    def get_service_bundle(self, limit: int = 20, skip: int = 10, service_type: ServiceType = None):
        bundles = self.session.query(Bundles)
        count = 0
        if service_type is None:
            count = bundles.count()
            bundles = bundles.offset(skip).limit(limit).all()
        count = bundles.filter(Bundles.bundle_type == service_type).count()

        bundles = bundles.filter(Bundles.bundle_type == service_type).offset(skip).limit(limit).all()
        return {
            'data': [ServiceBundleDTO.from_orm(bundle) for bundle in bundles],
            'total': count
        }

    # Laboratory Bundle Repositories
    def add_lab_bundle(self, lab_bundle_item: LabBundleCollectionDTO):
        bundle = LabBundleCollection(**lab_bundle_item.dict(exclude_unset=True))
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

    def get_lab_bundles(self, limit: int = 20, skip: int = 0) -> List:
        bundles = self.get_service_bundle(limit, skip, ServiceType.Laboratory)

        lab_bundles = []
        for bundle in bundles['data']:
            cols = [
                    LabBundleCollection.id,
                    LabBundleCollection.bundles_id,
                    LabBundleCollection.lab_service_id,
                    LabService.lab_service_name
                ]
            lab_bundle_collection = self.session.query(*cols)\
                .select_from(LabBundleCollection)\
                .join(LabService, LabService.id == LabBundleCollection.lab_service_id)\
                .filter(LabBundleCollection.bundles_id == bundle.id).all()
            lbc = [LabBundleCollectionDTO.from_orm(bdl) for bdl in lab_bundle_collection]

            # if len(lbc) > 0:
            bundle = bundle.dict()
            bundle["lab_collections"] = lbc
            lab_bundles.append(
                bundle
            )
        return {
            'data': lab_bundles,
            'total': bundles["total"]
        }

    def delete_lab_bundle(self, lab_collection_id: int):
        bundle = self.session.query(LabBundleCollection).filter(LabBundleCollection.id == lab_collection_id).first()
        if bundle:
            self.session.delete(bundle)
            self.session.commit()
            # self.session.refresh()
            return True
        return False
