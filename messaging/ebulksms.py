import httpx

from dtos.messaging.ebulk import EbulkSMSDTO


async def send_data(payload: EbulkSMSDTO):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.ebulksms.com/sendsms.json",
            json=payload.model_dump()
        )

    return {
        "external_response": response.json()
    }