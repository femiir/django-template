from procrastinate.contrib.django import app
from services.twilio.send_sms import TwilioSMSService


@app.task
def send_sms_task(to_number: str, message: str):
    sms_service = TwilioSMSService()
    response = sms_service.send_sms(to_number, message)
    return response