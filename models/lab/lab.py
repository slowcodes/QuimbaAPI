# from datetime import datetime
import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SqlEnum, Text, \
    UniqueConstraint, Boolean

from db import Base
from enum import Enum
from sqlalchemy.orm import relationship

from models.mixins import SoftDelMixin


class Laboratory(Base):
    __tablename__ = "laboratory"

    id = Column(Integer, primary_key=True, index=True)
    lab_name = Column(String(100), nullable=False, unique=True)
    lab_desc = Column(String(200))

    lab_service = relationship('LabService', back_populates="laboratory", uselist=True)
    __table_args__ = (UniqueConstraint("lab_name", name="uq_lab_name"),)


class LabServiceGroup(Base):
    __tablename__ = "lab_service_group"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50))
    group_desc = Column(String(100))


class LabType(str, Enum):
    Experiment = 'Experiment'
    Observation = 'Observation'


class LabService(Base, SoftDelMixin):
    __tablename__ = "lab_service"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("laboratory.id", ondelete="cascade"))
    lab_service_name = Column(String(100))
    lab_service_desc = Column(String(150))
    lab_type = Column(SqlEnum(LabType), default=LabType.Experiment)
    service_id = Column(Integer, ForeignKey("service_listing.service_id", ondelete="cascade"), unique=True)

    laboratory = relationship("Laboratory", back_populates="lab_service")
    # business_service = relationship("Business_Service", uselist=False, back_populates="lab_service")
    lab_service_group_tag = relationship("LabServiceGroupTag", back_populates="lab_service")
    lab_service_queue = relationship("LabServicesQueue", back_populates="lab_service")
    business_service = relationship("BusinessServices", back_populates="lab_service", uselist=False, lazy="selectin")
    lab_experiments = relationship("LabServiceExperiment", uselist=True)


class LabObservationResultTemplate(Base):
    __tablename__ = "lab_observation_result_template"

    id = Column(Integer, primary_key=True, index=True)
    # lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade"))
    template = Column(Text)
    template_desc = Column(String(150))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))

    user = relationship("User")



class LabServiceGroupTag(Base):
    __tablename__ = "lab_service_group_tag"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_group = Column(Integer, ForeignKey("lab_service_group.id", ondelete="cascade"))
    lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade"))

    lab_service = relationship("LabService", back_populates="lab_service_group_tag")
    group = relationship("LabServiceGroup")


class Experiment(Base):
    __tablename__ = "lab_experiment"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, default='Methodology/Experiment')
    use_only_dynamic_param = Column(Boolean, default=False)

    parameters = relationship("ExperimentParameter", back_populates="lab_experiment")
    dynamic_param_type = relationship("ExperimentDynamicParamType", back_populates="experiment", uselist=False)
    dynamic_parameters = relationship("DynamicParameter", back_populates="lab_experiment", uselist=True)


class DynamicParameterType(str, Enum):
    Drugs = 'Drugs'
    Strings = 'Strings'


class ExperimentDynamicParamType(Base):
    __tablename__ = "lab_experiment_dynamic_param_type"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("lab_experiment.id", ondelete="cascade"))
    param_type = Column(SqlEnum(DynamicParameterType))

    # relationship
    experiment = relationship("Experiment", back_populates="dynamic_param_type")

class DynamicParameter(Base):
    __tablename__ = "lab_dynamic_experiment_parameter"

    id = Column(Integer, primary_key=True, index=True)
    parameter = Column(String(50))
    parameter_value = Column(String(50))
    lab_service_queue_id = Column(Integer, ForeignKey("lab_service_queue.id", ondelete="cascade"))
    exp_id = Column(Integer, ForeignKey("lab_experiment.id", ondelete="cascade"))

    lab_service_queue = relationship("LabServicesQueue", back_populates="dynamic_parameters")
    lab_experiment = relationship("Experiment", back_populates="dynamic_parameters")


class ParameterType(str, Enum):
    Number = 'Number'
    Ratio = 'Ratio'
    Description = 'Description'
    Exclusive_Options = 'Exclusive_Options'
    Inclusive_Options = 'Inclusive_Options'


class ExperimentParameter(Base):
    __tablename__ = "lab_experiment_parameter"

    id = Column(Integer, primary_key=True, index=True)
    parameter = Column(String(50))
    measuring_unit = Column(String(50))
    parameter_type = Column(SqlEnum(ParameterType))
    exp_id = Column(Integer, ForeignKey("lab_experiment.id", ondelete="cascade"))
    stacking_order = Column(Integer, default=0)  # This is used to determine the order of parameters when displaying results

    lab_experiment = relationship("Experiment", back_populates="parameters")
    boundary = relationship("ExperimentParameterBounds", back_populates="parameter", uselist=True)


class LabServiceExperiment(Base):
    __tablename__ = "lab_service_experiment"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade"))
    experiment_id = Column(Integer, ForeignKey("lab_experiment.id", ondelete="cascade"))

    experiment = relationship("Experiment", uselist=False)


class BoundaryType(str, Enum):
    Normal = 'Normal'
    Abnormal = 'Abnormal'
    Invalid = 'Invalid'


class ExperimentParameterBounds(Base):
    __tablename__ = "lab_experiment_parameter_bounds"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("lab_experiment_parameter.id", ondelete="cascade"))
    upper_bound = Column(String(50))  # String because fractions like 1/3 should be held in original format
    lower_bound = Column(String(50))
    boundary_type = Column(SqlEnum(BoundaryType))

    parameter = relationship("ExperimentParameter", back_populates="boundary", uselist=False)


class LabResultExperiments(Base):
    __tablename__ = "lab_result_experiments"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("lab_collected_sample.id", ondelete="cascade"))


class Lab_Collected_Result(Base):
    __tablename__ = "lab_collected_result"

    id = Column(Integer, primary_key=True, index=True)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    issued_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    collected_by = Column(Integer)  # Column(Integer, ForeignKey("Client.id", ))


class QueueStatus(str, Enum):
    All = 'All'
    Waiting = 'Waiting' # suspended
    Processed = 'Processed'
    Processing = 'Processing'
    Cancelled = 'Cancelled'


class QueuePriority(str, Enum):
    Normal = 'Normal'
    High = 'High'
    Low = 'Low'


class LabServicesQueue(Base):
    __tablename__ = "lab_service_queue"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(SqlEnum(QueuePriority), default=QueuePriority.Normal)
    lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade"))
    scheduled_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)
    booking_id = Column(Integer, ForeignKey("service_booking_detail.id", ondelete="cascade"))

    lab_service = relationship("LabService", back_populates="lab_service_queue")
    booking = relationship("ServiceBookingDetail", back_populates="lab_service_queue")
    samples = relationship("CollectedSamples", back_populates="queue", uselist=True)
    lab_result = relationship("SampleResult", back_populates="queue",
                              uselist=False)  # observation based results may not have samples
    admission_lab_services = relationship("AdmissionLabServices", back_populates="lab_service_queue", uselist=False)
    dynamic_parameters = relationship("DynamicParameter", back_populates="lab_service_queue", uselist=True)

    @property
    def sample(self):
        return self.samples[0] if self.samples else None


class SampleType(str, Enum):
    Whole_Blood = 'Whole blood'
    Serum = 'Serum'
    Plasma = 'Plasma'
    Capillary_Blood = 'Capillary blood'
    Random_Urine = 'Random urine'
    First_Morning_Urine = 'First morning urine'
    Timed_Urine = 'Timed urine'
    Catheterized_Urine = 'Catheterized urine'
    Stool = 'Stool (fecal)'
    Throat_Swabs = 'Throat swabs'
    Nasal_Nasopharyngeal_Swabs = 'Nasal/nasopharyngeal swabs'
    Wound_Swabs = 'Wound swabs'
    Urogenital_Swabs = 'Urogenital swabs'
    Cerebrospinal_Fluid = 'Cerebrospinal fluid'
    Pleural_Fluid = 'Pleural fluid'
    Peritoneal_Fluid = 'Peritoneal fluid'
    Pericardial_Fluid = 'Pericardial fluid'
    Synovial_Fluid = 'Synovial fluid'
    Bronchoalveolar_Lavage = 'Bronchoalveolar lavage'
    biopsy = 'Biopsy'
    Sputum = 'Sputum - Mucus from the lungs'
    Hair = 'Hair'
    Nail = 'Nail'
    Amniotic_Fluid = 'Amniotic fluid'
    Saliva = 'Saliva'
    Semen = 'Semen'
    Tissue = 'Tissue'
    Bone_Marrow = 'Bone marrow'
    Breast_Milk = 'Breast milk'


class CollectedSamples(Base):
    __tablename__ = "lab_collected_sample"

    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("lab_service_queue.id", ondelete="cascade"))
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    sample_type = Column(SqlEnum(SampleType, name="sampletype"))
    collected_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    container_label = Column(String(50))
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)

    user = relationship("User")
    queue = relationship("LabServicesQueue", back_populates="samples", uselist=False)


class ExperimentResultReading(Base):
    __tablename__ = "lab_experiment_result_reading"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("lab_experiment_parameter.id", ondelete="cascade"))
    parameter_value = Column(Text)
    result_id = Column(Integer, ForeignKey("lab_sample_result.id", ondelete="cascade"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sample_result = relationship("SampleResult", back_populates="experiment_readings")
    parameter = relationship("ExperimentParameter")


class ResultStatus(str, Enum):
    Issued = 'Issued'
    Archived = 'Archived'
    Ready = 'Ready',
    Approved = 'Approved'  # Approved for release


class SampleResult(Base):
    __tablename__ = "lab_sample_result"

    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("lab_service_queue.id",
                                          ondelete="cascade"))  # some results may not be linked to samples. Eg observation based results
    created_at = Column(DateTime, default=datetime.date.today())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus), default=ResultStatus.Ready)

    user = relationship("User")
    queue = relationship("LabServicesQueue", back_populates="lab_result", uselist=False)
    experiment_readings = relationship("ExperimentResultReading", back_populates="sample_result", uselist=True)
    verification = relationship("LabVerifiedResult", back_populates="sample_result", uselist=False)

    @property
    def dynamic_parameters(self):
        return self.queue.dynamic_parameters if self.queue else []


class LabVerifiedResult(Base):
    __tablename__ = "lab_verified_result"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("lab_sample_result.id", ondelete="cascade"))
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus), default=ResultStatus.Ready)  # This is only useful at the frontend

    user = relationship("User")
    sample_result = relationship("SampleResult", back_populates="verification", uselist=False)


class LabResultLog(Base):
    __tablename__ = "lab_result_logs"

    id = Column(Integer, primary_key=True, index=True)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade"))
    logged_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    action = Column(SqlEnum(ResultStatus))


class LabBundleCollection(Base):
    __tablename__ = "lab_service_bundle_collection"

    id = Column(Integer, primary_key=True, index=True)
    bundles_id = Column(Integer, ForeignKey("service_bundle.id", ondelete="cascade"))
    lab_service_id = Column(Integer, ForeignKey("lab_service.service_id", ondelete="cascade"))

    bundle = relationship("Bundles", back_populates="lab_service_bundle")
    # business_service = relationship("BusinessServices")
    lab_service = relationship("LabService", uselist=False)


class ApprovedLabBookingResult(Base):
    __tablename__ = "lab_approved_booking_result"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade"), unique=True)
    approved_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus))

    booking = relationship("ServiceBooking", back_populates="result_approval", uselist=False)
    user = relationship("User")
