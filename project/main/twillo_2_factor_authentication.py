import random

from twilio.rest import TwilioRestClient
from twilio import TwilioRestException
from flask import session
from .. import config


def generate_code():
    return str(random.randrange(100000, 999999))

def send_sms(To_Number, Body):
    try:
        Twilio_Client = TwilioRestClient(config['production'].TWILIO_ACCOUNT_SID, config['production'].TWILIO_AUTH_TOKEN)
        Message = Twilio_Client.messages.create(to=To_Number,
                           from_=config['production'].TWILIO_NUMBER,
                           body=Body)
    except TwilioRestException as e:
        return False
    else:
        return True

def send_confirmation_code(To_Number):
    verification_code = generate_code()
    if send_sms(To_Number, verification_code) == True:
        session['verification_code'] = verification_code
    else:
        session['verification_code'] = None

