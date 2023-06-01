# from datetime import datetime
import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Double, Integer, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from db import Base
from enum import Enum
import models.services


class Laboratories(Base):
    __tablename__ = "Laboratories"

    id = Column(Integer, primary_key=True, index=True)
    lab_name = Column(String(40))
    lab_desc = Column(String(100))


class LabServiceGroup(Base):
    __tablename__ = "Lab_Service_Group"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50))
    group_desc = Column(String(100))


class LabServices(Base):
    __tablename__ = "Lab_Service"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("Laboratories.id", ondelete='CASCADE'))
    lab_service_name = Column(String(50))
    lab_service_desc = Column(String(150))
    service_id = Column(Integer, ForeignKey("Service_Listing.id", ondelete='CASCADE'))


class LabServiceGroupTag(Base):
    __tablename__ = "Lab_Service_Group_Tags"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_group = Column(Integer, ForeignKey("Lab_Service_Group.id", ondelete='CASCADE'))
    service_id = Column(Integer, ForeignKey("Lab_Service.id", ondelete='CASCADE'))


class LabResult(Base):
    __tablename__ = "Lab_Result"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)


class Experiments(Base):
    __tablename__ = "Lab_Experiment"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)


class ExperimentParameter(Base):
    __tablename__ = "Lab_Experiment_Parameter"

    id = Column(Integer, primary_key=True, index=True)
    lab_service_id = Column(Integer, ForeignKey("Lab_Service.id", ondelete='CASCADE'))
    parameter = Column(String(50))
    measuring_unit = Column(String(50))
    exp_id = Column(Integer, ForeignKey("Lab_Experiment_Parameter.id", ondelete='CASCADE'))


class BoundaryType(str, Enum):
    Normal = 'Normal'
    Abnormal = 'Abnormal'


class ExperimentParameterBounds(Base):
    __tablename__ = "Lab_Experiment_Parameter_Bounds"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("Lab_Experiment_Parameter.id", ondelete='CASCADE'))
    upper_bound = Column(Double)
    lower_bound = Column(Double)
    value_type = Column(SqlEnum(BoundaryType))


class LabResultExperiments(Base):
    __tablename__ = "Lab_Result_Experiments"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("Lab_Collected_Sample.id", ondelete='CASCADE'))


class LabVerifiedResult(Base):
    __tablename__ = "Lab_Verified_Result"

    id = Column(Integer, primary_key=True, index=True)
    verified_at = Column(Date, default=datetime.date.today())
    verified_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)


class Lab_Collected_Result(Base):
    __tablename__ = "Lab_Collected_Result"

    id = Column(Integer, primary_key=True, index=True)
    collected_at = Column(Date, default=datetime.date.today())
    issued_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    collected_by = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))


class QueueStatus(str, Enum):
    WAITING = 'Waiting'
    PROCESSED = 'Processed'
    PROCESSING = 'Processing'
    CANCELLED = 'Cancelled'


class LabServicesQueue(Base):
    __tablename__ = "Lab_Service_Queue"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("Laboratories.id", ondelete='CASCADE'))
    scheduled_at = Column(Date, default=datetime.date.today())
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.PROCESSING)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))


class SampleType(str, Enum):
    URINE = 'Urine'
    Feaces = 'Feaces'
    BLOOD = 'Blood'
    SKIN_SWAP = 'Skin Swap'


class CollectedSamples(Base):
    __tablename__ = "Lab_Collected_Sample"

    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("Lab_Service_Queue.id", ondelete='CASCADE'))
    collected_at = Column(Date, default=datetime.date.today())
    sample_type = Column(SqlEnum(SampleType))


class ExperimentResultReading(Base):
    __tablename__ = "Lab_Experiment_Result_Reading"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("Laboratories.id", ondelete='CASCADE'))
    parameter_value = Column(String(100))
    sample_id = Column(Integer, ForeignKey("Lab_Collected_Sample.id", ondelete='CASCADE'))
    created_at = Column(Date, default=datetime.date.today())


class SampleResult(Base):
    __tablename__ = "Lab_Sample_Result"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("Lab_Collected_Sample.id", ondelete='CASCADE'))
    created_at = Column(Date, default=datetime.date.today())
    created_by = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    comment = Column(Text)


