from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SqlEnum

from db import Base
from models.mixins import SoftDeleteMixin


class DataType(Enum):
    String = 'String'
    Integer = 'Integer'  # Staff
    Double = 'Double'
    Text = 'Text'
    JSON = 'JSON'


class UIControlType(Enum):
    TextField = 'TextField'
    TextArea = 'TextArea'
    Option = 'Option'
    CheckBox = 'CheckBox'
    File = 'File'


class ConfSetting(Base, SoftDeleteMixin):
    __tablename__ = "conf_setting"
    id = Column(Integer, primary_key=True, index=True)
    parameter = Column(String(30))
    param_desc = Column(String(200))
    data_type = Column(SqlEnum(DataType), nullable=False)
    param_value = Column(String(200))
    ui_control_type = Column(SqlEnum(UIControlType), default=UIControlType.TextField)
