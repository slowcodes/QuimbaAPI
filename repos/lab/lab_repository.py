from http.client import HTTPException
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from dtos.lab import LaboratoryGroupDTO, LaboratoryServiceDetailDTO, LabBundleCollectionDTO, LaboratoryDTO
from dtos.services import PriceCodeDTO
from models.client import *
from models.consultation import ConsultationQueue, InHours
from models.lab.lab import Laboratory, LabServiceGroup, LabService, LabServiceGroupTag, Experiment, ExperimentParameter, \
    ExperimentParameterBounds, LabServiceExperiment, SampleResult, CollectedSamples, LabServicesQueue, \
    LabBundleCollection
from models.services import PriceCode, BusinessServices, ServiceBooking, ServiceBookingDetail, Bundles, ServiceType, \
    BookingType
from models.transaction import Transaction
from repos.lab.experiment_repository import ExperimentRepository
from repos.services.price_repository import PriceRepository
from repos.services.service_repository import ServiceRepository


class LabRepository:

    def __init__(self, session: Session):
        self.session = session
        self.price_repository = PriceRepository(session)
        self.service_repo = ServiceRepository(session)
        self.experiment_repository = ExperimentRepository(session)

    def get_all_labs(self, skip, limit):
        return self.session.query(Laboratory).offset(skip).limit(limit).all()

    def get_laboratory_by_id(self, lab_id: int):
        return self.db.query(Laboratory).filter(Laboratory.id == lab_id).first()

    def get_all_labs_groups(self, skip, limit, keyword):
        if len(keyword) > 0:
            return dict(data=self.session.query(LabServiceGroup)
                        .filter(LabServiceGroup.group_name.ilike(f"%{keyword}%"))
                        .offset(skip).limit(limit).all(),
                        total=self.get_group_count(keyword))
        else:
            return dict(data=self.session.query(LabServiceGroup).offset(skip).limit(limit).all(),
                        total=self.get_group_count())

    def get_group_count(self, keyword: str = ''):
        return self.session.query(LabServiceGroup) \
            .filter(LabServiceGroup.group_name.ilike(f"%{keyword}%")).count() if (
                len(keyword) > 0) else self.session.query(
            LabServiceGroup).count()

    def get_lab_services(self, skip, limit, lab_id: int, keyword):
        cols = [
            LabService.id,
            LabService.lab_service_name,
            LabService.lab_service_desc,

            Laboratory.lab_name,
            BusinessServices.price_code,
            PriceCode.service_price,
            BusinessServices.ext_turn_around_time,
            BusinessServices.service_id
        ]

        # Build the query
        query = self.session.query(*cols).select_from(LabService) \
            .join(Laboratory, LabService.lab_id == Laboratory.id) \
            .join(BusinessServices, LabService.service_id == BusinessServices.service_id) \
            .join(PriceCode, BusinessServices.price_code == PriceCode.id)

        total = query.count()

        # Add conditions based on lab_id
        if lab_id != 0:
            query = query.filter(LabService.lab_id == lab_id)
        else:
            query = query.filter(LabService.lab_id > 0)

        total = query.count()

        # Apply search keyword if any
        if len(keyword.replace(' ', '')) > 2:
            # if search_text.lower() in item.lab_name.lower() or \
            #         search_text.lower() in item.lab_service_name.lower():
            #     rtn.append(data)
            query = query.filter(LabService.lab_service_name.ilike(f"%{keyword}%") |
                                 Laboratory.lab_name.ilike(f"%{keyword}%"))
            total = query.count()

        # Apply offset and limit
        result = query.offset(skip).limit(limit).all()
        # db.close()
        rtn = []

        for item in result:
            # group = db.query().select_from(LabServiceGroupTag).filter(LabServiceGroupTag.lab_service_id == lab_id)
            data = {
                'lab_id': item.service_id,
                'lab_name': item.lab_name,
                'lab_service_name': item.lab_service_name,
                'lab_service_desc': item.lab_service_desc,
                'price_code': item.price_code,
                'price': item.service_price,
                'eta': item.ext_turn_around_time,
                'service_id': item.service_id,  # this is needed to create service_booking_details.
                'lab_service_id': item.id  # this is needed to create lab_service_queue
            }
            rtn.append(data)
        return {'total': total, 'data': rtn}

    def get_lab_services_booking(self, transaction_id: int):
        cols = [
            ServiceBooking.id.label("booking_id"),
            ServiceBookingDetail.price_code,
            ServiceBookingDetail.id.label("booking_detail_id"),
            ServiceBookingDetail.service_id,
            ServiceBookingDetail.booking_type,
            LabService.lab_service_name,
            # ServiceBooking.client_id,
            PriceCode.service_price,
            PriceCode.id.label("service_price_code"),
            BusinessServices.ext_turn_around_time,
            Transaction.id.label("transaction_id")
        ]

        results = self.session.query(*cols).select_from(ServiceBookingDetail). \
            join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id). \
            join(PriceCode, PriceCode.id == ServiceBookingDetail.price_code). \
            join(Transaction, Transaction.id == ServiceBooking.transaction_id)

        lab_res = results.\
            join(LabService, LabService.service_id == ServiceBookingDetail.service_id). \
            join(BusinessServices, BusinessServices.service_id == ServiceBookingDetail.service_id). \
            filter(ServiceBooking.transaction_id == transaction_id). \
            filter(ServiceBookingDetail.booking_type == BookingType.Laboratory).all()

        bos = []
        for result in lab_res:
            bos.append({
                'booking_details_id': result.booking_detail_id,
                'service_id': result.service_id,
                'lab_service_name': result.lab_service_name,
                # 'lab_service_desc': result.lab_service_desc,
                'price_code': result.service_price_code,
                'price': result.service_price,
                'ext_turn_around_time': result.ext_turn_around_time
            })

        return bos

    def update_lab_service(self, id: int, lab_service: dict) -> Optional[LabService]:
        """Update a service by its ID."""
        service = self.session.query(LabService).filter(LabService.id == id).first()
        if service:
            for key, value in lab_service.items():
                if key and value:
                    setattr(service, key, value)
            self.session.commit()
            self.session.refresh(service)
            return service
        return None

    def update_lab_service_detail(self, lab_service_id: int, updated_service: LaboratoryServiceDetailDTO):
        # 1️⃣ Fetch the existing LabService record
        lab_service = self.session.query(LabService).filter(LabService.id == lab_service_id).first()
        if not lab_service:
            raise HTTPException(status_code=404, detail="Lab service not found")

        # 2️⃣ Update basic fields
        price_code = self.price_repository.create(PriceCodeDTO(
            service_price=updated_service.price,
            discount=updated_service.discount
        ))

        self.service_repo.update_business_service(lab_service.service_id, {
            'price_code': price_code.id,
            'ext_turn_around_time': updated_service.est_turn_around_time,
            'visibility': updated_service.visibility
        })
        lab_service.lab_service_name = updated_service.name
        lab_service.lab_service_desc = updated_service.description

        # update groups
        self.session.query(LabServiceGroupTag).filter(LabServiceGroupTag.lab_service_id == lab_service_id).delete()
        for group in updated_service.groups:
            new_group_tag = LabServiceGroupTag(
                lab_service_group=group,
                lab_service_id=lab_service_id
            )
            self.session.add(new_group_tag)
            self.session.commit()
            self.session.refresh(new_group_tag)

        # 4️⃣ Update experiments
        for exp in updated_service.exps:
            self.experiment_repository.update_experiment(lab_service.id, exp)

        # 5️⃣ Commit and refresh
        self.session.commit()
        self.session.refresh(lab_service)

        return updated_service

    def add_lab_services(self, laboratory_service: LaboratoryServiceDetailDTO):

        new_price_code = PriceCodeDTO(
            service_price=laboratory_service.price,
            discount=laboratory_service.discount
        )
        new_price_code = self.price_repository.create(new_price_code)
        new_business_details = BusinessServices(
            price_code=new_price_code.id,
            ext_turn_around_time=laboratory_service.est_turn_around_time,
            visibility=laboratory_service.visibility
        )

        self.session.add(new_business_details)
        self.session.commit()
        self.session.refresh(new_business_details)

        new_lab = LabService(
            lab_id=laboratory_service.lab_id,
            lab_service_name=laboratory_service.name,
            lab_service_desc=laboratory_service.description,
            service_id=new_business_details.service_id,
        )
        self.session.add(new_lab)
        self.session.commit()
        self.session.refresh(new_lab)

        for group in laboratory_service.groups:
            new_group_tag = LabServiceGroupTag(
                lab_service_group=group,
                lab_service_id=new_lab.id
            )
            self.session.add(new_group_tag)
            self.session.commit()
            self.session.refresh(new_group_tag)

        exps = []
        for experiment in laboratory_service.exps:
            new_experiment = Experiment(
                description=experiment.name
            )
            self.session.add(new_experiment)
            self.session.commit()
            self.session.refresh(new_experiment)

            exps.append(new_experiment.id)

            for parameter in experiment.parameter:
                new_parameter = ExperimentParameter(
                    parameter=parameter.name,
                    measuring_unit=parameter.unit,
                    exp_id=new_experiment.id,
                    parameter_type=parameter.type
                )
                self.session.add(new_parameter)
                self.session.commit()
                self.session.refresh(new_parameter)

                for boundary in parameter.boundary:
                    new_boundary = ExperimentParameterBounds(
                        parameter_id=new_parameter.id,
                        upper_bound=boundary.upper_bound,
                        lower_bound=boundary.lower_bound,
                        boundary_type=boundary.boundary_type
                    )
                    self.session.add(new_boundary)
                    self.session.commit()

        for exp in exps:
            new_lab_experiment = LabServiceExperiment(
                lab_service_id=new_lab.id,
                experiment_id=exp
            )
            self.session.add(new_lab_experiment)
            self.session.commit()
            self.session.refresh(new_experiment)
        return True

    def add_lab(self, lab: LaboratoryDTO) -> Boolean:
        counter = self.session.query(Laboratory).where(Laboratory.lab_name == lab.lab).count()
        if counter <= 0:
            new_lab = Laboratory(
                lab_name=lab.lab,
                lab_desc=lab.description
            )
            self.session.add(new_lab)
            self.session.commit()
            self.session.refresh(new_lab)
            return True

        return False

    def update_lab(self, lab: LaboratoryDTO) -> Boolean:
        labx = self.session.query(Laboratory).filter(Laboratory.id == lab.id).first()

        if not labx:
            return False  # Return False when lab does not exist

        try:
            if lab.lab:
                labx.lab_name = lab.lab
            if lab.description:
                labx.lab_desc = lab.description

            self.session.commit()
            return True  # Indicate success
        except SQLAlchemyError:
            self.session.rollback()
            return False  # Indicate failure

    def add_lab_group(self, grp: LaboratoryGroupDTO) -> Boolean:
        counter = self.session.query(LabServiceGroup).where(LabServiceGroup.group_name == grp.group_name).count()
        if counter <= 0:
            new_grp = LabServiceGroup(group_name=grp.group_name, group_desc=grp.group_desc)
            self.session.add(new_grp)
            self.session.commit()
            self.session.refresh(new_grp)
            return True

        return False

    def get_lab_group(self, lab_id: int):
        cols = [
            LabServiceGroup.id,
            LabServiceGroup.group_name,
            LabServiceGroupTag.lab_service_id
        ]

        rs = self.session.query(*cols).select_from(LabServiceGroupTag) \
            .join(LabServiceGroup, LabServiceGroup.id == LabServiceGroupTag.lab_service_group) \
            .filter(LabServiceGroupTag.lab_service_id == lab_id).all()

        rtn = []
        for items in rs:
            rtn.append(items.group_name)

        return rtn;

    def get_lab_service_details_by_service_id(self, service_id: int):
        lab_service = self.session.query(LabService).filter(LabService.service_id == service_id).first()
        if lab_service:
            return self.get_lab_service_details(lab_service.id)
        return None

    def get_lab_service_details(self, lab_id: int):

        bs = aliased(BusinessServices)
        ls = aliased(LabService)
        pc = aliased(PriceCode)

        cols = [
            ls.lab_service_name,
            ls.lab_service_desc,
            ls.id,
            ls.service_id,
            bs.visibility,
            bs.ext_turn_around_time,
            # bs.price_code,
            bs.service_id,
            pc.service_price,
            pc.discount,
            pc.id.label("price_code"),
        ]
        rs = self.session.query(*cols).select_from(ls). \
            join(bs, ls.service_id == bs.service_id). \
            join(pc, bs.price_code == pc.id). \
            filter(ls.id == lab_id).first()

        if rs:
            return {
                'discount': rs.discount,
                'name': rs.lab_service_name,
                'description': rs.lab_service_desc,
                'est_turn_around_time': rs.ext_turn_around_time,
                'price': rs.service_price,
                'lab_service_id': rs.id,
                'groups': self.get_lab_group(lab_id),
                'discounted_packages': self.service_repo.get_discounted_packages(rs.service_id),
                'exps': self.experiment_repository.get_lab_experiments(lab_id),
                'lab_id': lab_id,
                'price_code': rs.price_code,
                'visibility': rs.visibility,
                'service_id': rs.service_id,
                'result_summary_text': self.get_result_summary_text(lab_id)
            }

        return None

    def get_result_summary_text(self, lab_service_id: int):

        cols = [SampleResult.id, SampleResult.comment]
        rs = self.session.query(*cols) \
            .select_from(LabServicesQueue) \
            .join(CollectedSamples, CollectedSamples.queue_id == LabServicesQueue.id) \
            .join(SampleResult, CollectedSamples.id == SampleResult.sample_id) \
            .filter(LabServicesQueue.lab_service_id == lab_service_id) \
            .all()
        results = [row._asdict() for row in rs]
        return results
