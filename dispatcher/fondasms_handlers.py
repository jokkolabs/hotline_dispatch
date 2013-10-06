#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import random

from django.conf import settings
from fondasms.utils import datetime_from_timestamp

# from douentza.models import HotlineRequest
# from douentza.utils import (event_type_from_message,
#                             is_valid_number,
#                             number_is_blacklisted,
#                             operator_from_mali_number)
# from douentza.utils import normalize_phone_number
from dispatcher.models import HotlineEvent
from dispatcher.utils import (NB_CHARS_HOTLINE,
                              operator_from_mali_number,
                              make_ushahidi_request,
                              is_valid_number,
                              send_notification,
                              number_is_blacklisted,
                              normalize_phone_number)


class UnableToCreateHotlineRequest(Exception):
    pass

# place holder for incoming phone numbers (phone device)
# with operator
INCOMING_NUMBERS_BY_OPERATOR = {}
INCOMING_NUMBERS_WITH_OPERATOR = {}


def event_type_from_message(message):
    message = message.strip()
    call_me_tpl_orange = "Peux-tu me rappeler au numero suivant"
    charge_me_tpl_orange = "Peux-tu recharger mon compte au numero suivant"
    call_me_tpl_malitel = "Rappellez moi s'il vous plait au numero suivant"
    am_tpl_orange = "Messagerie Vocale:"

    if message.startswith(call_me_tpl_orange) \
       or message.startswith(call_me_tpl_malitel):
        return HotlineEvent.TYPE_CALL_ME
    if message.startswith(charge_me_tpl_orange):
        return HotlineEvent.TYPE_CHARGE_ME
    if message.startswith(am_tpl_orange):
        return HotlineEvent.TYPE_RING
    if not message:
        return HotlineEvent.TYPE_RING
    if len(message) < NB_CHARS_HOTLINE:
        return HotlineEvent.TYPE_SMS_HOTLINE
    # if len(message) > NB_CHARS_USHAHIDI:
    #     return HotlineEvent.TYPE_SMS_USHAHIDI
    return HotlineEvent.TYPE_SMS_UNKNOWN



def automatic_reply_handler(payload):
    # called by automatic reply logic
    # if settings.FONDA_SEND_AUTOMATIC_REPLY_VIA_HANDLER
    # Can be used to fetch or forge reply when we need more than
    # the static FONDA_AUTOMATIC_REPLY_TEXT
    return None


def handle_incoming_sms(payload):
    # on SMS received
    return handle_sms_call(payload)


def handle_incoming_call(payload):
    # on call received
    return handle_sms_call(payload, event_type=HotlineEvent.TYPE_RING)


def handle_sms_call(payload, event_type=None):

    identity = normalize_phone_number(payload.get('from').strip())
    if not is_valid_number(identity) or number_is_blacklisted(identity):
        return

    message = payload.get('message').strip()
    if not len(message):
        message = None

    if event_type is None:
        event_type = event_type_from_message(message)

    phone_number = payload.get('phone_number')
    timestamp = payload.get('timestamp')
    received_on = datetime_from_timestamp(timestamp)
    operator = operator_from_mali_number(identity)

    try:
        existing = HotlineEvent.objects.get(identity=identity,
                                            processed=False)
    except HotlineEvent.DoesNotExist:
        existing = None

    # if same number calls again before previous request has been treated
    # we just update the date of the event.
    if existing:
        print(existing)
        existing.received_on = received_on
        existing.save()
        return

    try:
        event = HotlineEvent.objects.create(
            identity=identity,
            event_type=event_type,
            hotline_number=phone_number,
            received_on=received_on,
            sms_message=message,
            operator=operator)
    except:
        return

    if event.event_type == HotlineEvent.TYPE_SMS_USHAHIDI:
        event.processed = False
        make_ushahidi_request(event)

    send_notification(event)
    return


def handle_outgoing_status_change(payload):
    # we don't store outgoing messages for now
    return


def handle_device_status_change(payload):
    # we don't track device changes for now
    return


def check_meta_data(payload):
    # we don't track device changes for now
    return


def reply_with_phone_number(payload):
    end_user_phone = payload.get('from')
    if end_user_phone is not None:
        return get_phone_number_for(operator_from_mali_number(end_user_phone))
    return None


def get_phone_number_for(operator):
    return random.choice(INCOMING_NUMBERS_BY_OPERATOR.get(operator, [None])) or None

for number in settings.FONDA_INCOMING_NUMBERS:
    operator = operator_from_mali_number(number)
    if not operator in INCOMING_NUMBERS_BY_OPERATOR.keys():
        INCOMING_NUMBERS_BY_OPERATOR.update({operator: []})
    INCOMING_NUMBERS_BY_OPERATOR[operator].append(number)
    INCOMING_NUMBERS_WITH_OPERATOR.update({number: operator})
