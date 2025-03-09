from typing import List

from sqlalchemy.orm import Session, aliased

from commands.lab import LaboratoryGroupDTO, CommandLaboratoryService, LabBundleCollectionDTO
from models.client import *
from models.lab.lab import Laboratory, LabServiceGroup, LabService, LabServiceGroupTag, Experiment, ExperimentParameter, \
    ExperimentParameterBounds, LabServiceExperiment, SampleResult, CollectedSamples, LabServicesQueue, \
    LabBundleCollection
from models.services import PriceCode, BusinessServices, ServiceBooking, ServiceBookingDetail, Bundles, ServiceType
from models.transaction import Transaction
from repos.services.service_repository import ServiceRepository


class LabRepository:
    def __init__(self, session: Session):
        self.session = session
        self.service_repo = ServiceRepository(session)


    def get_all_labs(self, skip, limit):
        return self.session.query(Laboratory).offset(skip).limit(limit).all()

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

        # sys.setrecursionlimit(20)
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
                'service_id': item.service_id,
                'lab_service_id': item.id
            }
            rtn.append(data)
        return {'total': total, 'data': rtn}

    def get_lab_services_booking(self, transaction_id: int):
        cols = [
            ServiceBooking.id.label("booking_id"),
            ServiceBookingDetail.price_code,
            ServiceBookingDetail.id.label("booking_detail_id"),
            ServiceBookingDetail.service_id,
            LabService.lab_service_name,
            # ServiceBooking.client_id,
            PriceCode.service_price,
            BusinessServices.ext_turn_around_time,
            Transaction.id.label("transaction_id")
        ]

        results = self.session.query(*cols).select_from(ServiceBookingDetail). \
            join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id). \
            join(PriceCode, PriceCode.id == ServiceBookingDetail.price_code). \
            join(Transaction, Transaction.id == ServiceBooking.transaction_id). \
            join(LabService, LabService.service_id == ServiceBookingDetail.service_id). \
            join(BusinessServices, BusinessServices.service_id == ServiceBookingDetail.service_id). \
            filter(ServiceBooking.transaction_id == transaction_id).all()

        bos = []
        for result in results:
            bos.append({
                'booking_details_id': result.booking_detail_id,
                'service_id': result.service_id,
                'lab_service_name': result.lab_service_name,
                # 'lab_service_desc': result.lab_service_desc,
                'price_code': result.price_code,
                'price': result.service_price,
                'ext_turn_around_time': result.ext_turn_around_time
            })

        return bos

    def add_lab_services(self, laboratory_service: CommandLaboratoryService):
        new_price_code = PriceCode(
            service_price=laboratory_service.price,
            discount=laboratory_service.discount
        )
        self.session.add(new_price_code)
        self.session.commit()
        self.session.refresh(new_price_code)

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

    def add_lab(self, lab: Laboratory) -> Boolean:
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
            bs.price_code,
            bs.service_id,
            pc.service_price,
            pc.discount,
            pc.id,
        ]
        rs = self.session.query(*cols).select_from(ls). \
            join(bs, ls.service_id == bs.price_code). \
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
                'exps': self.get_lab_experiments(lab_id),
                'lab_id': lab_id,
                'visibility': rs.visibility,
                'service_id': rs.service_id,
                'result_summary_text': self.get_result_summary_text(lab_id)
            }
        print('Nothing data found')
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

    def get_lab_experiments(self, lab_id: int):
        cols = [
            Experiment.id,
            Experiment.description,
            LabServiceExperiment.lab_service_id.label("service_id")
        ]

        rs = self.session.query(*cols).select_from(Experiment) \
            .join(LabServiceExperiment, Experiment.id == LabServiceExperiment.experiment_id) \
            .filter(LabServiceExperiment.lab_service_id == lab_id).all()

        rtn = []
        for items in rs:
            rtn.append(
                {
                    'name': items.description,
                    'key': items.service_id,
                    'parameter': self.get_experiment_parameter(items.id)
                })

        return rtn;

    def get_experiment_parameter(self, exp_id: int):
        cols = [
            ExperimentParameter.id,
            ExperimentParameter.parameter,
            ExperimentParameter.measuring_unit,
            ExperimentParameter.parameter_type,

        ]
        rs = self.session.query(*cols).select_from(ExperimentParameter).filter(
            ExperimentParameter.exp_id == exp_id).all()
        parameter = []
        for param in rs:
            parameter.append({
                'boundary': self.get_parameter_boundaries(param.id),
                'name': param.parameter,
                'unit': param.measuring_unit,
                'type': param.parameter_type,
                'paramKey': param.id
            })
        return parameter

    def get_parameter_boundaries(self, param_id: int):
        cols = [
            ExperimentParameterBounds.id,
            ExperimentParameterBounds.lower_bound,
            ExperimentParameterBounds.upper_bound,
            ExperimentParameterBounds.boundary_type
        ]
        rs = self.session.query(*cols) \
            .select_from(ExperimentParameterBounds) \
            .filter(ExperimentParameterBounds.parameter_id == param_id).all()
        boundaries = []
        for bounds in rs:
            boundaries.append({
                'lower_bound': bounds.lower_bound,
                'upper_bound': bounds.upper_bound,
                'boundary_type': bounds.boundary_type
            })
        return boundaries
