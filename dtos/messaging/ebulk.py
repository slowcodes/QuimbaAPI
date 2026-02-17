from pydantic import BaseModel, Field
from typing import List


class SmsAuthDTO(BaseModel):
    username: str
    apikey: str


class SmsMessageDTO(BaseModel):
    sender: str
    messagetext: str
    flash: str = Field(default="0")


class SmsRecipientDTO(BaseModel):
    msidn: str
    msgid: str


class SmsRecipientsDTO(BaseModel):
    gsm: List[SmsRecipientDTO]


class SmsPayloadDTO(BaseModel):
    auth: SmsAuthDTO
    message: SmsMessageDTO
    recipients: SmsRecipientsDTO
    dndsender: str = Field(default="0")


class EbulkSMSDTO(BaseModel):
    SMS: SmsPayloadDTO
