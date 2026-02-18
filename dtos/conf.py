from typing import Optional

from pydantic import BaseModel

from models.conf import DataType, UIControlType


class ConfSettingDTO(BaseModel):
    id: Optional[int] = None
    parameter: str
    param_desc: Optional[str] = None
    data_type: DataType
    param_value: str
    ui_control_type: UIControlType
