# from datetime import datetime
import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Double, Integer, String, DateTime, Date, Enum as SqlEnum, Text, \
    BLOB, UniqueConstraint
from sqlalchemy.orm import relationship

from db import Base
from enum import Enum
import models.services
from sqlalchemy.orm import relationship


class Laboratory(Base):
    __tablename__ = "laboratory"

    id = Column(Integer, primary_key=True, index=True)
    lab_name = Column(String(100), nullable=False, unique=True)
    lab_desc = Column(String(200))

    lab_service = relationship('LabService', back_populates="Laboratory")
    __table_args__ = (UniqueConstraint("lab_name", name="uq_lab_name"),)


class LabServiceGroup(Base):
    __tablename__ = "lab_service_group"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50))
    group_desc = Column(String(100))


class LabService(Base):
    __tablename__ = "lab_service"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("laboratory.id", ondelete="cascade"))
    lab_service_name = Column(String(100))
    lab_service_desc = Column(String(150))
    service_id = Column(Integer, ForeignKey("service_listing.service_id", ondelete="cascade" ))

    Laboratory = relationship("Laboratory", back_populates="lab_service")
    # business_service = relationship("Business_Service", uselist=False, back_populates="lab_service")
    lab_service_group_tag = relationship("LabServiceGroupTag", back_populates="lab_service")

class LabServiceGroupTag(Base):
    __tablename__ = "lab_service_group_tag"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_group = Column(Integer, ForeignKey("lab_service_group.id", ondelete="cascade" ))
    lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade" ))

    lab_service = relationship("LabService", back_populates="lab_service_group_tag")


class LabResult(Base):
    __tablename__ = "lab_result"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="cascade" ))
    comment = Column(Text)


class Experiment(Base):
    __tablename__ = "lab_experiment"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, default='Methodology/Experiment')


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
    exp_id = Column(Integer, ForeignKey("lab_experiment.id", ondelete="cascade" ))


class LabServiceExperiment(Base):
    __tablename__ = "lab_service_experiment"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade"))
    experiment_id = Column(Integer, ForeignKey("lab_experiment.id", ondelete="cascade" ))


class BoundaryType(str, Enum):
    Normal = 'Normal'
    Abnormal = 'Abnormal'
    Invalid = 'Invalid'


class ExperimentParameterBounds(Base):
    __tablename__ = "lab_experiment_parameter_bounds"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("lab_experiment_parameter.id", ondelete="cascade" ))
    upper_bound = Column(String(50))    # String because fractions like 1/3 should be held in original format
    lower_bound = Column(String(50))
    boundary_type = Column(SqlEnum(BoundaryType))


class LabResultExperiments(Base):
    __tablename__ = "lab_result_experiments"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("lab_collected_sample.id", ondelete="cascade"))


class Lab_Collected_Result(Base):
    __tablename__ = "lab_collected_result"

    id = Column(Integer, primary_key=True, index=True)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    issued_by = Column(Integer, ForeignKey("users.id", ondelete="cascade" ))
    collected_by = Column(Integer)  # Column(Integer, ForeignKey("Client.id", ))


class QueueStatus(str, Enum):
    All = 'All'
    Waiting = 'Waiting'
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
    lab_service_id = Column(Integer, ForeignKey("lab_service.id", ondelete="cascade"  ))
    scheduled_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)
    booking_id = Column(Integer, ForeignKey("service_booking_detail.id", ondelete="cascade" ))


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
    queue_id = Column(Integer, ForeignKey("lab_service_queue.id", ondelete="cascade" ))
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    sample_type = Column(SqlEnum(SampleType, name="sampletype") )
    collected_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    container_label = Column(String(50))
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)


class ExperimentResultReading(Base):
    __tablename__ = "lab_experiment_result_reading"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("lab_experiment_parameter.id", ondelete="cascade"  ))
    parameter_value = Column(String(100))
    sample_id = Column(Integer, ForeignKey("lab_collected_sample.id", ondelete="cascade" ))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ResultStatus(str, Enum):
    Issued = 'Issued'
    Archived = 'Archived'
    Ready = 'Ready',
    Approved = 'Approved'  # Approved for release


class SampleResult(Base):
    __tablename__ = "lab_sample_result"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("lab_collected_sample.id", ondelete="cascade" ))
    created_at = Column(DateTime, default=datetime.date.today())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus), default=ResultStatus.Ready)

    class Config:
        orm_mode = True


class LabVerifiedResult(Base):
    __tablename__ = "lab_verified_result"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("lab_sample_result.id", ondelete="cascade"  ))
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="cascade" ))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus))

    class Config:
        orm_mode = True


class LabResultLog(Base):
    __tablename__ = "lab_result_logs"

    id = Column(Integer, primary_key=True, index=True)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade"))
    logged_by = Column(Integer, ForeignKey("users.id", ondelete="cascade" ))
    action = Column(SqlEnum(ResultStatus))

    class Config:
        orm_mode = True

class LabBundleCollection(Base):
    __tablename__ = "lab_service_bundle_collection"

    id = Column(Integer, primary_key=True, index=True)
    bundles_id = Column(Integer, ForeignKey("service_bundle.id", ondelete="cascade" ))
    lab_service_id = Column(Integer, ForeignKey("service_listing.service_id", ondelete="cascade"))

    bundle = relationship("Bundles", back_populates="lab_service_bundle")
    class Config:
        orm_mode = True

class ApprovedLabBookingResult(Base):
    __tablename__ = "approved_lab_booking_result"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade" ))
    approved_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="cascade" ))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus))

    class Config:
        orm_mode = True
