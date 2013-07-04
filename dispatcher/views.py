#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import json
import datetime

from django.conf import settings
from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from dispatcher.models import (HotlineEvent, HotlineVolunteer, HotlineResponse,
                               Topics, Entity, BlackList)
from dispatcher.utils import (NB_NUMBERS, NB_CHARS_HOTLINE, NB_CHARS_USHAHIDI,
                              operator_from_mali_number,
                              clean_phone_number,
                              make_ushahidi_request,
                              is_valid_number,
                              send_notification,
                              operators, ANSWER, COUNTRY_PREFIX,
                              join_phone_number,
                              number_is_blacklisted,
                              count_unknown_sms,
                              count_unarchived_sms,
                              count_unprocessed)

LOGIN_URL = '/login/'
Ring_anwers = []


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
def smssync(request):

    def http_response(is_processed, resp_messages=[]):
        global Ring_anwers
        response = {'payload': {'success': bool(is_processed)}}
        if len(Ring_anwers):
            while True:
                try:
                    identity = Ring_anwers.pop()
                    resp_messages.append((identity, ANSWER))
                except IndexError:
                    break
        if resp_messages:
            response['payload'].update({'task': 'send',
                                        'secret': settings.USHAHIDI_SECRET,
                                        'messages': [{'to': to, 'message': text}
                                                     for to, text in resp_messages]})
        from pprint import pprint as pp; pp(response)
        return HttpResponse(json.dumps(response), mimetype='application/json')

    if not request.method == 'POST':
        return http_response(True)

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
    if not is_valid_number(identity) or number_is_blacklisted(identity):
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

    return http_response(processed, resp_messages=[(identity, ANSWER)])


def ringsync_status(request):

    return HttpResponse("OK")


def ringsync(request, call_number, call_timestamp):

    global Ring_anwers

    processed = True

    prefix, phone_number = clean_phone_number(call_number)
    if not prefix:
        prefix = COUNTRY_PREFIX
    identity = join_phone_number(prefix, phone_number)

    # SPAM?
    if not is_valid_number(identity) or number_is_blacklisted(identity):
        return HttpResponse("OK", status=200)

    operator = operator_from_mali_number(identity)
    try:
        # android sends timestamp in microseconds
        received_on = datetime.datetime.fromtimestamp(int(call_timestamp) / 1000)
    except:
        received_on = None

    try:
        existing = HotlineEvent.objects.get(identity=identity,
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
                identity=identity,
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
        Ring_anwers.append(identity)
        return HttpResponse("OK", status=201)

    return HttpResponse("NOT", status=301)


@login_required(login_url=LOGIN_URL)
def dashboard(request):

    context = {'page': 'dashboard',
               'nbsms': count_unknown_sms(),
               'nbarchive': count_unarchived_sms(),
               'nbunprocessed': count_unprocessed(),
               'operators': [(operator,
                              HotlineEvent.objects.filter(operator=operator,
                                                          processed=False,
                                                          event_type__in=HotlineEvent.HOTLINE_TYPES).count())
                             for operator in operators()]}

    if request.method == 'POST':

        try:
            nb_numbers = int(request.POST.get('nb_numbers', NB_NUMBERS))
        except ValueError:
            nb_numbers = NB_NUMBERS

        operator = request.POST.get('operator_request')
        if not operator in operators():
            context.update({'error': "L'opérateur demandé (%s) "
                                     "n'est pas correct" % operator})

        events = HotlineEvent.objects.filter(operator=operator,
                                             processed=False,
                                             event_type__in=HotlineEvent.HOTLINE_TYPES) \
                                     .order_by('received_on')[:nb_numbers]

        for event in events:
            event.processed = True
            event.volunteer = request.user
            event.save()

        context.update({'events': events,
                        'requested': True,
                        'operator': operator,
                        # 'user_number': user_number,
                        'nb_numbers': nb_numbers})

    return render(request, "dashboard.html", context)


@login_required(login_url=LOGIN_URL)
def sms_check(request, event_filter=HotlineEvent.TYPE_SMS_UNKNOWN):

    context = {'page': 'sms', 'nbsms': count_unknown_sms(),
               'nbarchive': count_unarchived_sms(),
               'nbunprocessed': count_unprocessed()}

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


@login_required(login_url=LOGIN_URL)
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


@login_required(login_url=LOGIN_URL)
def change_password(request):
    context = {'page': 'password', 'nbsms': count_unknown_sms(),
               'nbunprocessed': count_unprocessed(),
               'nbarchive': count_unarchived_sms()}

    class ChangePasswordForm(forms.Form):

        old_password = forms.CharField(label="Mot de passe actuel",
                                       max_length=100,
                                       widget=forms.PasswordInput)
        new_password = forms.CharField(label="Nouveau mot de passe",
                                       max_length=100,
                                       widget=forms.PasswordInput)
        new_password_verify = forms.CharField(label="Nouveau mot de passe (vérification)",
                                              max_length=100, widget=forms.PasswordInput)

        def clean(self):
            cleaned_data = super(ChangePasswordForm, self).clean()

            new_password = cleaned_data.get('new_password')
            new_password_verify = cleaned_data.get('new_password_verify')

            if new_password != new_password_verify:
                raise forms.ValidationError("Les nouveaux mot de passe ne sont pas identiques")
            return cleaned_data

        def clean_old_password(self):
            old_password = self.cleaned_data.get('old_password')
            if not request.user.check_password(old_password):
                raise forms.ValidationError("Mot de passe incorrect.")

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            messages.success(request, "Le mot de passe a été changé.")
            return redirect('home')
    else:
        form = ChangePasswordForm()

    context.update({'form': form})

    return render(request, "change_password.html", context)


@login_required(login_url=LOGIN_URL)
def data_entry(request):
    ''' Enter Data for calls made by the volunteers

        Step 1: Pick a volunteer to enter data for.
        Step 2: List all calls made by the chosen volunteer
        Step 3: Enter data for a specific call.
        This creates a HotlineResponse object. '''

    class HotlineResponseForm(forms.Form):
        ''' Used to easily enter data for calls made by volunteers. '''

        request_id = forms.IntegerField(widget=forms.HiddenInput)
        response_date = forms.DateTimeField(label="Date de l'appel",
                                            initial=lambda: datetime.datetime.now(),
                                            help_text="Format: JJ/MM/AAAA",
                                            widget=forms.SplitDateTimeWidget)
        duration = forms.IntegerField(label="Durée (approx.)",
                                      help_text="En nombre de minutes arrondis (ex. 2 pour 1min:35s et 1 pour 1min:29s)")
        topics = forms.MultipleChoiceField(label="Questions",
                                           choices=[(t.slug, t.display_name())
                                           for t in Topics.objects.all()],
                                           widget=forms.CheckboxSelectMultiple)
        age = forms.IntegerField(label="Age", required=False)
        sex = forms.ChoiceField(label="Sexe", choices=HotlineResponse.SEXES.items(),
                                required=False, initial=HotlineResponse.SEX_UNKNOWN)
        region = forms.ChoiceField(label="Région",
                                   choices=[(None, " --- ")] + [(e.slug, e.name)
                                   for e in Entity.objects.filter(type=Entity.TYPE_REGION)])
        cercle = forms.CharField(label="Cercle", widget=forms.Select, required=False)
        commune = forms.CharField(label="Commune", widget=forms.Select, required=False)
        village = forms.CharField(label="Village", widget=forms.Select, required=False)

        def clean_village(self):
            ''' Returns a Village Entity from the multiple selects '''
            location = None
            levels = ['region', 'cercle', 'commune', 'village']
            while len(levels) and (location is None or location == '00000000'):
                location = self.cleaned_data.get(levels.pop())
            try:
                return Entity.objects.get(slug=location)
            except Entity.DoesNotExist:
                raise forms.ValidationError("Localité incorrecte.")

        def clean_request_id(self):
            ''' Return a HotlineEvent from the id '''
            try:
                return HotlineEvent.objects.get(id=int(self.cleaned_data.get('request_id')))
            except HotlineEvent.DoesNotExist:
                raise forms.ValidationError("Évennement incorrect")

    context = {'page': 'data_entry', 'nbsms': count_unknown_sms(),
               'nbunprocessed': count_unprocessed(),
               'nbarchive': count_unarchived_sms(),
               'volunteers': [(vol, HotlineEvent.objects.filter(volunteer=vol,
                                                                processed=True,
                                                                archived=False).count())
                              for vol in HotlineVolunteer.objects.filter(is_active=True)]}

    volunteer = None
    events = []

    # Send volunteer to template if it's in GET
    if request.GET.get('volunteer'):
        volunteer = get_object_or_404(HotlineVolunteer,
                                      username=request.GET.get('volunteer'))

    if volunteer:
        events = HotlineEvent.objects.filter(volunteer=volunteer,
                                             processed=True,
                                             archived=False)

    # If POST, we received data for a HotlineResponse
    if request.method == 'POST':
        form = HotlineResponseForm(request.POST)
        if form.is_valid():

            event_request = form.cleaned_data.get('request_id')
            event_request.archived = True

            event_response = HotlineResponse.objects \
                .create(request=event_request,
                        response_date=form.cleaned_data.get('response_date'),
                        age=form.cleaned_data.get('age'),
                        sex=form.cleaned_data.get('sex'),
                        duration=form.cleaned_data.get('duration'),
                        location=form.cleaned_data.get('village'))
            # topics
            event_response.save()
            for topic_slug in form.cleaned_data.get('topics'):
                event_response.topics.add(Topics.objects.get(slug=topic_slug))
            event_response.save()

            event_request.save()

            messages.success(request, "Appel %s enregistré" % event_request)

            # redirect to the page with the volunteer GET param
            response = redirect('data_entry')
            response['Location'] += '?volunteer=%s' % event_request.volunteer.username
            return response
    else:
        form = HotlineResponseForm()

    context.update({'volunteer': volunteer,
                    'events': events,
                    'form': form})

    return render(request, "data_entry.html", context)


def entities_api(request, parent_slug=None):
    ''' JSON list of Entity whose parent has the slug provided '''

    response = [{'slug': '00000000', 'name': "---"}] + \
        [{'slug': e.slug, 'name': e.name}
            for e in Entity.objects.filter(parent__slug=parent_slug)]

    return HttpResponse(json.dumps(response), mimetype='application/json')


@login_required(login_url=LOGIN_URL)
def blacklist(request):
    context = {'page': 'blackList',
               'nbarchive': count_unarchived_sms(),
               'nbunprocessed': count_unprocessed(),
               'nbsms': count_unknown_sms()}

    if request.method == 'POST':
        identity = request.POST.get('identity').strip()
        ind, number = clean_phone_number(identity)
        identity = join_phone_number(ind, number)
        if not BlackList.objects.filter(identity=identity).count():
            BlackList.objects.create(identity=identity)
        else:
            b = BlackList.objects.get(identity=identity)
            b.call_count += 1
            b.save()
            messages.success(request, "%s ajouté dans la liste noire" % b.identity)

    context.update({'blacknums': BlackList.objects.all()})

    return render(request, "blacklist.html", context)


@login_required(login_url=LOGIN_URL)
def status(request):
    context = {'page': 'status',
               'nbarchive': count_unarchived_sms(),
               'nbunprocessed': count_unprocessed(),
               'nbsms': count_unknown_sms()}
    last_event = HotlineEvent.objects.order_by('-received_on')[0]
    total_events = HotlineEvent.objects.count()
    for operator in operators():
        if operator == 'orange':
            count_orange = HotlineEvent.objects.filter(operator=operator).count()
        else:
            count_malitel = HotlineEvent.objects.filter(operator=operator).count()

    per_event_type = {}
    for event_type in HotlineEvent.TYPES:
        per_event_type.update({event_type[0]:
                               (event_type[1], HotlineEvent.objects.filter(event_type=event_type[0]).count())})

    untreated = HotlineEvent.objects.filter(processed=False)
    untreated_count = untreated.count()
    not_archived = HotlineEvent.objects.filter(archived=False).count()
    sex_unknow = HotlineResponse.objects.filter(sex=HotlineResponse.SEX_UNKNOWN).count()
    sex_male = HotlineResponse.objects.filter(sex=HotlineResponse.SEX_MALE).count()
    sex_female = HotlineResponse.objects.filter(sex=HotlineResponse.SEX_FEMALE).count()

    context.update({'last_event': last_event,
                    'total_events': total_events,
                    'per_event_type': per_event_type,
                    'untreated': untreated,
                    'count_orange': count_orange,
                    'count_malitel': count_malitel,
                    'untreated_count': untreated_count,
                    'sex_unknow': sex_unknow,
                    'sex_male': sex_male,
                    'sex_female': sex_female,
                    'not_archived': not_archived})

    return render(request, "status.html", context)
