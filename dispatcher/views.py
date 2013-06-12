#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import json
import datetime

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from dispatcher.models import HotlineEvent
from dispatcher.utils import (NB_NUMBERS, NB_CHARS_HOTLINE, NB_CHARS_USHAHIDI,
                              operator_from_mali_number,
                              all_volunteers_numbers,
                              clean_phone_number,
                              make_ushahidi_request,
                              is_valid_number,
                              send_notification)


def event_type_from_message(message):
    message = message.strip()
    call_me_tpl_orange = "Peux-tu me rappeler au numero suivant"
    charge_me_tpl_orange = "Peux tu recharger mon compte au numero suivant"
    call_me_tpl_malitel = "Rappellez moi s'il vous plait au numero suivant"

    if message.startswith(call_me_tpl_orange) \
       or message.startswith(call_me_tpl_malitel):
        return HotlineEvent.TYPE_CALL_ME
    if message.startswith(charge_me_tpl_orange):
        return HotlineEvent.TYPE_CHARGE_ME
    if not message:
        return HotlineEvent.TYPE_RING
    if len(message) < NB_CHARS_HOTLINE:
        return HotlineEvent.TYPE_SMS_HOTLINE
    if len(message) > NB_CHARS_USHAHIDI:
        return HotlineEvent.TYPE_SMS_USHAHIDI
    return HotlineEvent.TYPE_SMS_UNKNOWN


@csrf_exempt
@require_POST
def smssync(request):

    def http_response(is_processed):
        response = {'payload': {'success': bool(is_processed)}}
        return HttpResponse(json.dumps(response))

    processed = False

    sent_timestamp = request.POST.get('sent_timestamp')
    try:
        received_on = datetime.datetime.fromtimestamp(int(sent_timestamp) / 1000)
    except ValueError:
        received_on = None
    event_type = event_type_from_message(request.POST.get('message'))
    identity = request.POST.get('from')
    sent_to = request.POST.get('sent_to')
    message = request.POST.get('message')
    operator = operator_from_mali_number(identity)

    # skip SPAM
    if not is_valid_number(identity):
        return http_response(True)

    try:
        existing = HotlineEvent.objects.get(identity=identity,
                                            processed=False)
    except HotlineEvent.DoesNotExist:
        existing = None

    # if same number calls again before previous request has been treated
    # we just update the date of the event.
    if existing:
        existing.received_on = received_on
        existing.save()
        return http_response(True)

    try:
        event = HotlineEvent.objects.create(
            identity=identity,
            event_type=event_type,
            hotline_number=sent_to,
            received_on=received_on,
            sms_message=message,
            operator=operator)
        processed = True
    except:
        return http_response(False)

    if event.event_type == HotlineEvent.TYPE_SMS_USHAHIDI:
        event.processed = False
        processed = make_ushahidi_request(event)

    send_notification(event)

    return http_response(processed)


def ringsync_status(request):

    return HttpResponse("OK")


def ringsync(request, call_number, call_timestamp):

    processed = True
    operator = operator_from_mali_number(call_number)
    try:
        # android sends timestamp in microseconds
        received_on = datetime.datetime.fromtimestamp(int(call_timestamp) / 1000)
    except:
        received_on = None

    try:
        existing = HotlineEvent.objects.get(identity=call_number,
                                            processed=False)
    except HotlineEvent.DoesNotExist:
        existing = None

    if existing:
        existing.received_on = received_on
        existing.save()
        processed = True
    else:
        try:
            event = HotlineEvent.objects.create(
                identity=call_number,
                event_type=HotlineEvent.TYPE_RING,
                hotline_number=None,
                received_on=received_on,
                sms_message=None,
                operator=operator)
            processed = True
            send_notification(event)
        except:
            processed = False

    if processed:
        return HttpResponse("OK", status=201)

    return HttpResponse("NOT", status=301)


@login_required(login_url='/login/')
def dashboard(request):

    context = {}

    if request.method == 'POST':

        user_number = request.POST.get('number')
        ind, cleaned_phone_number = clean_phone_number(user_number)
        try:
            nb_numbers = int(request.POST.get('nb_numbers', NB_NUMBERS))
        except ValueError:
            nb_numbers = NB_NUMBERS

        if not cleaned_phone_number in all_volunteers_numbers():
            context.update({'error': "Le numéro %s ne fait pas partie "
                                     "des volontaires" % user_number})

        operator = operator_from_mali_number(user_number)

        events = HotlineEvent.objects.filter(operator=operator,
                                             processed=False,
                                             event_type__in=HotlineEvent.HOTLINE_TYPES) \
                                     .order_by('-received_on')[:nb_numbers]

        for event in events:
            event.processed = True
            event.save()

        context.update({'events': events,
                        'requested': True,
                        'operator': operator,
                        'user_number': user_number,
                        'nb_numbers': nb_numbers})

    return render(request, "dashboard.html", context)


@login_required(login_url='/login/')
def sms_check(request, event_filter=HotlineEvent.TYPE_SMS_UNKNOWN):

    context = {}

    if not event_filter in HotlineEvent.SMS_TYPES:
        event_filter = HotlineEvent.TYPE_SMS_UNKNOWN

    try:
        nb_numbers = int(request.POST.get('nb_numbers', NB_NUMBERS))
    except ValueError:
        nb_numbers = NB_NUMBERS
    events = HotlineEvent.objects.filter(processed=False,
                                         event_type=event_filter) \
                                 .order_by('-received_on')[:nb_numbers]

    context.update({'events': events,
                    'filter': event_filter,
                    'filters': [(HotlineEvent.TYPE_SMS_UNKNOWN, "À Trier"),
                                (HotlineEvent.TYPE_SMS_HOTLINE, "Hotline"),
                                (HotlineEvent.TYPE_SMS_USHAHIDI, "Ushahidi"),
                                (HotlineEvent.TYPE_SMS_SPAM, "SPAM")],
                    'requested': True,
                    'nb_numbers': nb_numbers})

    return render(request, "sms_check.html", context)


@login_required(login_url='/login/')
def sms_change_type(request, event_id, new_type,
                    return_to=HotlineEvent.TYPE_SMS_UNKNOWN):

    try:
        event = HotlineEvent.objects.get(id=int(event_id))
        event.event_type = new_type
        event.save()
    except (HotlineEvent.DoesNotExist, ValueError):
        pass

    if event and event.event_type == HotlineEvent.TYPE_SMS_USHAHIDI:
        make_ushahidi_request(event)

    return redirect('sms_filter', return_to)
