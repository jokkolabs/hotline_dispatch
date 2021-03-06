#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import json
import datetime


from django import forms
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from batbelt import to_timestamp

from dispatcher.models import (HotlineEvent, HotlineVolunteer, HotlineResponse,
                               Topics, Entity, BlackList, ResponseSMS)
from dispatcher.utils import (NB_NUMBERS, NB_CHARS_HOTLINE,
                              operator_from_mali_number,
                              clean_phone_number,
                              make_ushahidi_request,
                              is_valid_number,
                              send_notification,
                              operators, ANSWER, COUNTRY_PREFIX,
                              join_phone_number,
                              number_is_blacklisted,
                              datetime_range,
                              count_unarchived_sms,
                              get_default_context, stats_per_age,
                              EMPTY_ENTITY, topic_stats_details, regions_located_responses,
                              import_hotine_events)


@login_required()
def dashboard(request):

    context = get_default_context(page='dashboard')

    context.update({'operators':
                    [(operator, HotlineEvent.objects.filter(operator=operator,
                                                            processed=False,
                                                            event_type__in=HotlineEvent.HOTLINE_TYPES).count())
                     for operator in operators()]})

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


@login_required()
def sms_check(request, event_filter=HotlineEvent.TYPE_SMS_UNKNOWN):

    context = get_default_context(page='sms')

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
                                (HotlineEvent.TYPE_CHARGE_ME, "Peux-tu recharger mon compte?"),
                                (HotlineEvent.TYPE_SMS_SPAM, "SPAM")],
                    'requested': True,
                    'nb_numbers': nb_numbers})

    return render(request, "sms_check.html", context)


@login_required()
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


@login_required()
def change_password(request):
    context = get_default_context(page='password')

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


@login_required()
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
                                            help_text="Format: JJ/MM/AAAA",
                                            widget=forms.SplitDateTimeWidget)
        duration = forms.IntegerField(label="Durée (approx.)",
                                      help_text="En nombre de minutes arrondis "
                                                "(ex. 2 pour 1min:35s et 1 pour 1min:29s)")
        topics = forms.MultipleChoiceField(label="Questions",
                                           choices=[(t.slug, t.display_name())
                                           for t in Topics.objects.order_by('slug')],
                                           widget=forms.CheckboxSelectMultiple)
        age = forms.IntegerField(label="Age", required=False)
        sex = forms.ChoiceField(label="Sexe", choices=HotlineResponse.SEXES.items(),
                                required=False, initial=HotlineResponse.SEX_UNKNOWN)
        region = forms.ChoiceField(label="Région",
                                   choices=[(EMPTY_ENTITY, "INCONNUE")] + [(e.slug, e.name)
                                   for e in Entity.objects.filter(type=Entity.TYPE_REGION)])
        cercle = forms.CharField(label="Cercle", widget=forms.Select, required=False)
        commune = forms.CharField(label="Commune", widget=forms.Select, required=False)
        village = forms.CharField(label="Village", widget=forms.Select, required=False)

        def clean_village(self):
            ''' Returns a Village Entity from the multiple selects '''
            is_empty = lambda l: l is None or l == EMPTY_ENTITY
            location = None
            levels = ['region', 'cercle', 'commune', 'village']
            while len(levels) and is_empty(location):
                location = self.cleaned_data.get(levels.pop()) or None

            if is_empty(location):
                return None

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

    context = get_default_context(page='data_entry')
    context.update({'volunteers': [(vol, HotlineEvent.objects.filter(volunteer=vol,
                                                                     processed=True,
                                                                     answer__isnull=True).count())
                                   for vol in HotlineVolunteer.objects.filter(is_active=True)]})

    volunteer = None
    events = []

    # Send volunteer to template if it's in GET
    if request.GET.get('volunteer'):
        volunteer = get_object_or_404(HotlineVolunteer,
                                      username=request.GET.get('volunteer'))

    if volunteer:
        events = HotlineEvent.objects.filter(volunteer=volunteer,
                                             processed=True,
                                             answer__isnull=True)

    # If POST, we received data for a HotlineResponse
    if request.method == 'POST':
        form = HotlineResponseForm(request.POST)
        if form.is_valid():

            event_request = form.cleaned_data.get('request_id')

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


@login_required()
def entities_api(request, parent_slug=None):
    ''' JSON list of Entity whose parent has the slug provided '''

    response = [{'slug': EMPTY_ENTITY, 'name': "INCONNU"}] + \
        [{'slug': e.slug, 'name': e.name}
            for e in Entity.objects.filter(parent__slug=parent_slug)]

    return HttpResponse(json.dumps(response), mimetype='application/json')


@login_required()
def blacklist(request):
    context = get_default_context(page='blacklist')

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


def get_status_context():
    ''' return the context for status '''
    context = {}
    try:
        last_event = HotlineEvent.objects.latest('received_on')
    except HotlineEvent.DoesNotExist:
        last_event = []

    total_events = HotlineEvent.objects.count()
    total_unique_number = HotlineEvent.objects.values('identity').distinct().count()

    per_event_type = {}
    for event_type in HotlineEvent.TYPES:
        per_event_type.update({event_type[0]:
                               (event_type[1],
                                HotlineEvent.objects.filter(event_type=event_type[0]).count())})

    untreated_count = HotlineEvent.objects.filter(processed=False).count()
    not_archived = count_unarchived_sms()
    sex_unknown = HotlineResponse.objects.filter(sex=HotlineResponse.SEX_UNKNOWN).count() + \
                                          len([1 for e in HotlineEvent.objects.all() if not e.archived])
    sex_male = HotlineResponse.objects.filter(sex=HotlineResponse.SEX_MALE).count()
    sex_female = HotlineResponse.objects.filter(sex=HotlineResponse.SEX_FEMALE).count()

    unknown_count = HotlineResponse.objects.filter(location=None).count()
    total = HotlineResponse.objects.all().count()
    try:
        unknown_percent = unknown_count * 100 / total
    except ZeroDivisionError:
        unknown_percent = 0

    under_18 = stats_per_age(0, 18)
    stats_19_25 = stats_per_age(19, 25)
    stats_26_30 = stats_per_age(26, 30)
    stats_31_35 = stats_per_age(31, 35)
    stats_36_40 = stats_per_age(36, 40)
    stats_41_45 = stats_per_age(41, 45)
    stats_46_50 = stats_per_age(46, 50)
    stats_55_56 = stats_per_age(51, 55)
    other_56 = stats_per_age(56, 180)

    unknown_age = HotlineResponse.objects.filter(age=None).count()
    try:
        unknown_age_percent = unknown_age * 100 / total
    except ZeroDivisionError:
        unknown_age_percent = 0

    context.update({'last_event': last_event,
                    'total_events': total_events,
                    'total_unique_number': total_unique_number,
                    'per_event_type': per_event_type,
                    'untreated_count': untreated_count,
                    'sex_unknown': sex_unknown,
                    'sex_male': sex_male,
                    'sex_female': sex_female,
                    'operators': [(operator, HotlineEvent.objects.filter(operator=operator).count())
                                  for operator in operators()],
                    'under_18': under_18,
                    'stats_19_25': stats_19_25,
                    'stats_26_30': stats_26_30,
                    'stats_31_35': stats_31_35,
                    'stats_36_40': stats_36_40,
                    'stats_41_45': stats_41_45,
                    'stats_46_50': stats_46_50,
                    'stats_55_56': stats_55_56,
                    'other_56': other_56,
                    'unknown_age': unknown_age,
                    'unknown_age_percent': unknown_age_percent,
                    'topics_stats_details': topic_stats_details(),
                    'regions_located_responses': [regions_located_responses(region)
                                                  for region in list(Entity.objects.filter(type='region'))] +
                                                 [("Inconnue", unknown_count, unknown_percent)],
                    'not_archived': not_archived})
    return context


@login_required()
def status(request):
    context = get_default_context(page='status')

    context.update(get_status_context())

    return render(request, "status.html", context)


@login_required()
def import_event(request):
    context = get_default_context(page='import_event')

    def handle_uploaded_file(f):
        """ stores temporary file as a real file for form upload """
        fname = '/tmp/form_%s.xls' % datetime.datetime.now().strftime('%s')
        destination = open(fname, 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
        return fname

    context.update(get_status_context())

    if request.method == "POST":

        if 'csv_file' in request.FILES:
            filepath = handle_uploaded_file(request.FILES['csv_file'])

        try:
            result = import_hotine_events(filepath)
            context.update(result)
        except UnboundLocalError:
            context.update({'error_message': 'Aucun fichier sélectionné', 'nbok': 0})

        context.update({"result": True})

    return render(request, "import_event.html", context)


def exported_status(request):
    context = get_default_context(page='status')

    context.update(get_status_context())

    return render(request, "status_for_export.html", context)


def get_graph_context():
    date_start_end = lambda d, s=True: \
        datetime.datetime(int(d.year), int(d.month), int(d.day),
                          0 if s else 23, 0 if s else 59, 0 if s else 59)

    try:
        start = HotlineEvent.objects.order_by('received_on')[0].received_on
    except IndexError:
        start = datetime.datetime.today()

    requests = []
    responses = []

    for date in datetime_range(start):
        ts = int(to_timestamp(date)) * 1000
        qcount = HotlineEvent.objects.filter(received_on__gte=date_start_end(date),
                                             received_on__lt=date_start_end(date, False)).count()
        scount = HotlineResponse.objects.filter(response_date__gte=date_start_end(date),
                                                response_date__lt=date_start_end(date, False)).count()
        requests.append((ts, qcount))
        responses.append((ts, scount))
    data_event = {'requests': requests,
                  'responses': responses}

    return data_event


@login_required()
def graph_data(request):
    ''' Return graph data in json '''

    return HttpResponse(json.dumps(get_graph_context()), mimetype='application/json')
