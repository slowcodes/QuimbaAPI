# from datetime import datetime
import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Double, Integer, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from sqlalchemy.orm import relationship

from db import Base
from enum import Enum
import models.services


class Laboratory(Base):
    __tablename__ = "Laboratory"

    id = Column(Integer, primary_key=True, index=True)
    lab_name = Column(String(40))
    lab_desc = Column(String(100))

    lab_service = relationship('LabService', back_populates="Laboratory")


class LabServiceGroup(Base):
    __tablename__ = "Lab_Service_Group"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50))
    group_desc = Column(String(100))


class LabService(Base):
    __tablename__ = "Lab_Service"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("Laboratory.id", ondelete='CASCADE'))
    lab_service_name = Column(String(50))
    lab_service_desc = Column(String(150))
    service_id = Column(Integer, ForeignKey("Service_Listing.service_id", ondelete='CASCADE'))

    Laboratory = relationship("Laboratory", back_populates="lab_service")
    # business_service = relationship("Business_Service", uselist=False, back_populates="lab_service")


class LabServiceGroupTag(Base):
    __tablename__ = "Lab_Service_Group_Tag"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_group = Column(Integer, ForeignKey("Lab_Service_Group.id", ondelete='CASCADE'))
    lab_service_id = Column(Integer, ForeignKey("Lab_Service.id", ondelete='CASCADE'))


class LabResult(Base):
    __tablename__ = "Lab_Result"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)


class Experiment(Base):
    __tablename__ = "Lab_Experiment"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)


class ParameterType(str, Enum):
    Number = 'Number'
    Ratio = 'Ratio'
    Description = 'Description'


class ExperimentParameter(Base):
    __tablename__ = "Lab_Experiment_Parameter"

    id = Column(Integer, primary_key=True, index=True)
    parameter = Column(String(50))
    measuring_unit = Column(String(50))
    parameter_type = Column(SqlEnum(ParameterType))
    exp_id = Column(Integer, ForeignKey("Lab_Experiment.id", ondelete='CASCADE'))


class LabServiceExperiment(Base):
    __tablename__ = "Lab_Service_Experiment"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_id = Column(Integer, ForeignKey("Lab_Service.id", ondelete='CASCADE'))
    experiment_id = Column(Integer, ForeignKey("Lab_Experiment.id", ondelete='CASCADE'))


class BoundaryType(str, Enum):
    Normal = 'Normal'
    Abnormal = 'Abnormal'
    Invalid = 'Invalid'


class ExperimentParameterBounds(Base):
    __tablename__ = "Lab_Experiment_Parameter_Bounds"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("Lab_Experiment_Parameter.id", ondelete='CASCADE'))
    upper_bound = Column(Double)
    lower_bound = Column(Double)
    boundary_type = Column(SqlEnum(BoundaryType))


class LabResultExperiments(Base):
    __tablename__ = "Lab_Result_Experiments"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("Lab_Collected_Sample.id", ondelete='CASCADE'))


class Lab_Collected_Result(Base):
    __tablename__ = "Lab_Collected_Result"

    id = Column(Integer, primary_key=True, index=True)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    issued_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    collected_by = Column(Integer)  # Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))


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
    __tablename__ = "Lab_Service_Queue"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(SqlEnum(QueuePriority), default=QueuePriority.Normal)
    lab_service_id = Column(Integer, ForeignKey("Laboratory.id", ondelete='CASCADE'))
    scheduled_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)
    booking_id = Column(Integer, ForeignKey("Service_Booking_Detail.id", ondelete='CASCADE'))


class SampleType(str, Enum):
    Urine = 'Urine'
    Feaces = 'Feaces'
    Blood = 'Blood'
    Skin_Swap = 'Skin Swap'
    Saliva = 'Saliva'


class CollectedSamples(Base):
    __tablename__ = "Lab_Collected_Sample"

    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("Lab_Service_Queue.id", ondelete='CASCADE'))
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    sample_type = Column(SqlEnum(SampleType))
    collected_by = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"))
    container_label = Column(String(50))
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)


class ExperimentResultReading(Base):
    __tablename__ = "Lab_Experiment_Result_Reading"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("Lab_Experiment_Parameter.id", ondelete='CASCADE'))
    parameter_value = Column(String(100))
    sample_id = Column(Integer, ForeignKey("Lab_Collected_Sample.id", ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ResultStatus(str, Enum):
    Issued = 'Issued'
    Archived = 'Archived'
    Ready = 'Ready',
    Approved = 'Approved' # Approved for release


class SampleResult(Base):
    __tablename__ = "Lab_Sample_Result"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("Lab_Collected_Sample.id", ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.date.today())
    created_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus), default=ResultStatus.Ready)


class LabVerifiedResult(Base):
    __tablename__ = "Lab_Verified_Result"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("Lab_Sample_Result.id", ondelete='CASCADE'))
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    verified_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus))


class LabResultLog(Base):
    __tablename__ = "Lab_Result_Logs"

    id = Column(Integer, primary_key=True, index=True)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id"))
    logged_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    action = Column(SqlEnum(ResultStatus))


class LabBundleCollection(Base):
    __tablename__ = "Lab_Service_Bundle_Collection"

    id = Column(Integer, primary_key=True, index=True)
    bundles_id = Column(Integer, ForeignKey("Service_Bundle.id", ondelete='CASCADE'))
    lab_service_id = Column(Integer, ForeignKey("Service_Listing.service_id", ondelete='CASCADE'))


class ApprovedLabBookingResult(Base):
    __tablename__ = "Approved_Lab_Booking_Result"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))
    approved_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)
    status = Column(SqlEnum(ResultStatus))

    class Config:
        orm_mode = True
