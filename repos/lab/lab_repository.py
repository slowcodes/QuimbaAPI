from http.client import HTTPException
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from dtos.lab import LaboratoryGroupDTO, LaboratoryServiceDetailDTO, LaboratoryDTO, LabServiceDTO
from dtos.services import PriceCodeDTO
from models.client import *
from models.lab.lab import Laboratory, LabServiceGroup, LabService, LabServiceGroupTag, Experiment, ExperimentParameter, \
    ExperimentParameterBounds, LabServiceExperiment, SampleResult, CollectedSamples, LabServicesQueue, LabType, \
    QueueStatus, ResultStatus
from models.services.services import PriceCode, BusinessServices, ServiceBooking, ServiceBookingDetail, BookingType
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

    def get_all_labs(self, skip, limit, keyword: Optional[str] = None):
        query = self.session.query(Laboratory)
        if keyword:
            query = query.filter(Laboratory.lab_name.ilike(f"%{keyword}%"))
        return query.offset(skip).limit(limit).all()

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

    def soft_delete_lab_service_detail(self, lab_service_id: int) -> bool:
        # implement soft
        try:
            lab_service = (
                self.session.query(LabService)
                .filter(
                    LabService.id == lab_service_id,
                    LabService.deleted_at.is_(None)
                )
                .one_or_none()
            )

            if lab_service is None:
                return False

            lab_service.soft_delete()
            self.session.commit()
            return True
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def get_group_count(self, keyword: str = ''):
        return self.session.query(LabServiceGroup) \
            .filter(LabServiceGroup.group_name.ilike(f"%{keyword}%")).count() if (
                len(keyword) > 0) else self.session.query(
            LabServiceGroup).count()

    def get_lab_services(self, skip, limit, lab_id: int, keyword):
        query = self.session.query(LabService).filter(LabService.deleted_at.is_(None))

        # Add conditions based on lab_id
        if lab_id != 0:
            query = query.filter(LabService.lab_id == lab_id)

        # Apply search keyword if any
        if len(keyword.replace(' ', '')) > 2:
            query = query.filter(LabService.lab_service_name.ilike(f"%{keyword}%") |
                                 Laboratory.lab_name.ilike(f"%{keyword}%"))
        total = query.count()

        # Apply offset and limit
        query = query.offset(skip).limit(limit).all()

        data = [LabServiceDTO.from_orm(lb_service) for lb_service in query]
        return {'total': total, 'data': data}

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

        lab_res = results. \
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

    def get_current_state(self, lab_id: Optional[int]):
        """
        Returns counts of queue entries, collected samples, and results.
        If lab_id is falsy (0/None), counts are aggregated across all labs.
        """
        queue_query = (
            self.session.query(func.count(LabServicesQueue.id))
            .join(LabService, LabServicesQueue.lab_service_id == LabService.id)
        )

        sample_query = (
            self.session.query(func.count(CollectedSamples.id))
            .join(LabServicesQueue, CollectedSamples.queue_id == LabServicesQueue.id)
            .join(LabService, LabServicesQueue.lab_service_id == LabService.id)
            .filter(CollectedSamples.status == QueueStatus.Processing)
        )

        result_query = (
            self.session.query(func.count(SampleResult.id))
            .join(LabServicesQueue, SampleResult.queue_id == LabServicesQueue.id)
            .join(LabService, LabServicesQueue.lab_service_id == LabService.id)
            .filter(SampleResult.status == ResultStatus.Ready)
        )

        if lab_id:
            queue_query = queue_query.filter(LabService.lab_id == lab_id)
            sample_query = sample_query.filter(LabService.lab_id == lab_id)
            result_query = result_query.filter(LabService.lab_id == lab_id)

        return {
            'queue': queue_query.scalar() or 0,
            'collected_samples': sample_query.scalar() or 0,
            'results': result_query.scalar() or 0
        }

    def update_lab_service_detail(self, lab_service_id: int, updated_service: LabServiceDTO) -> LabServiceDTO:
        try:
            # 1️⃣ Fetch the existing LabService record
            lab_service = self.session.query(LabService).filter(LabService.id == lab_service_id).first()
            if not lab_service:
                raise HTTPException(status_code=404, detail="Lab service not found")

            # 2️⃣ Update basic fields
            price_code = PriceCode(
                service_price=updated_service.business_service.pc.service_price,
                discount=updated_service.business_service.pc.discount
            )
            self.session.add(price_code)
            self.session.flush()

            # 3️⃣ Update Business Service details
            business_service = self.session.query(BusinessServices).filter(
                BusinessServices.service_id == lab_service.service_id).first()
            business_service.price_code = price_code.id
            business_service.ext_turn_around_time = updated_service.business_service.ext_turn_around_time
            business_service.visibility = updated_service.business_service.visibility

            lab_service.lab_service_name = updated_service.lab_service_name
            lab_service.lab_service_desc = updated_service.lab_service_desc
            lab_service.lab_type = updated_service.lab_type
            lab_service.lab_id = updated_service.laboratory.id

            # update groups
            self.session.query(LabServiceGroupTag).filter(LabServiceGroupTag.lab_service_id == lab_service_id).delete()
            for group in updated_service.lab_service_group_tag:
                new_group_tag = LabServiceGroupTag(
                    lab_service_group=group.lab_service_group,
                    lab_service_id=lab_service_id
                )
                self.session.add(new_group_tag)

            if updated_service.lab_type == LabType.Observation:
                # clear experiments if lab type is Observation
                self.session.query(LabServiceExperiment).filter(LabServiceExperiment.lab_service_id == lab_service_id).delete()
            else:
                # 4️⃣ Update experiments
                for exp in updated_service.lab_experiments:
                    self.experiment_repository.update_experiment(lab_service.id, exp.experiment)

            # 5️⃣ Commit and refresh
            self.session.commit()
            self.session.refresh(lab_service)

            return updated_service
        except:
            self.session.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while updating the lab service")

    def add_lab_services(self, laboratory_service: LaboratoryServiceDetailDTO):
        try:
            new_price_code = PriceCodeDTO(
                service_price=laboratory_service.price,
                discount=laboratory_service.discount
            )
            new_price_code = self.price_repository.create(new_price_code)
            new_business_details = BusinessServices(
                price_code=new_price_code.id,
                ext_turn_around_time=laboratory_service.est_turn_around_time,
                visibility=laboratory_service.visibility,
                service_type='Laboratory',
            )

            self.session.add(new_business_details)
            self.session.flush()

            new_lab = LabService(
                lab_id=laboratory_service.lab_id,
                lab_type=laboratory_service.lab_type,
                lab_service_name=laboratory_service.name,
                lab_service_desc=laboratory_service.description,
                service_id=new_business_details.service_id,
            )
            self.session.add(new_lab)
            self.session.flush()

            for group in laboratory_service.groups:
                new_group_tag = LabServiceGroupTag(
                    lab_service_group=group,
                    lab_service_id=new_lab.id
                )
                self.session.add(new_group_tag)
                self.session.flush()

            exps = []
            for experiment in laboratory_service.exps:
                new_experiment = Experiment(
                    description=experiment.description
                )
                self.session.add(new_experiment)
                self.session.flush()

                exps.append(new_experiment.id)

                for parameter in experiment.parameters:
                    new_parameter = ExperimentParameter(
                        parameter=parameter.parameter,
                        measuring_unit=parameter.measuring_unit,
                        exp_id=new_experiment.id,
                        parameter_type=parameter.parameter_type,
                        stacking_order=parameter.stacking_order
                    )
                    self.session.add(new_parameter)
                    self.session.flush()

                    for boundary in parameter.boundary:
                        new_boundary = ExperimentParameterBounds(
                            parameter_id=new_parameter.id,
                            upper_bound=boundary.upper_bound,
                            lower_bound=boundary.lower_bound,
                            boundary_type=boundary.boundary_type
                        )
                        self.session.add(new_boundary)
                        self.session.flush()

            for exp in exps:
                new_lab_experiment = LabServiceExperiment(
                    lab_service_id=new_lab.id,
                    experiment_id=exp
                )
                self.session.add(new_lab_experiment)
                self.session.flush()

            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error occurred: {e}")
            return False

    def add_lab(self, lab: LaboratoryDTO) -> Boolean:
        counter = self.session.query(Laboratory).where(Laboratory.lab_name == lab.lab_name).count()
        if counter <= 0:
            new_lab = Laboratory(
                lab_name=lab.lab_name,
                lab_desc=lab.lab_desc
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
            return LabServiceDTO.from_orm(lab_service)
        return None

    def get_lab_service_details(self, lab_id: int):
        lab_service = self.session.query(LabService).filter(LabService.id == lab_id).first()
        res = LabServiceDTO.from_orm(lab_service)
        print(lab_service.lab_service_name, '78', res.lab_service_name)

        return res

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
