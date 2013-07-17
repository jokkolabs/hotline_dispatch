#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import re
import json
import smtplib
import datetime
import zipfile

import requests
import unicodecsv
from django.conf import settings
from django.core import mail
from django.template import loader, Context
from django.contrib.sites.models import Site
from batbelt import to_timestamp


ORANGE = 'orange'
MALITEL = 'malitel'
FOREIGN = 'foreign'
NB_NUMBERS = 5
NB_CHARS_HOTLINE = 45
NB_CHARS_USHAHIDI = 100
NB_CHARS_VALID_NUMBER = 8
COUNTRY_PREFIX = '223'
ANSWER = "Merci de votre appel. La Hotline SOS Démocratie vous rappelle bientôt."
# ANSWER = "I ni cɛ. SOS Demokrasi mɔgɔ bɛ i wele sɔɔni."
EMPTY_ENTITY = '00000000'

ALL_COUNTRY_CODES = [1242, 1246, 1264, 1268, 1284, 1340, 1345, 1441, 1473,
                     1599, 1649, 1664, 1670, 1671, 1684, 1758, 1767, 1784,
                     1809, 1868, 1869, 1876, 1, 20, 212, 213, 216, 218, 220,
                     221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231,
                     232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242,
                     243, 244, 245, 248, 249, 250, 251, 252, 253, 254, 255,
                     256, 257, 258, 260, 261, 262, 263, 264, 265, 266, 267,
                     268, 269, 27, 290, 291, 297, 298, 299, 30, 31, 32, 33,
                     34, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359,
                     36, 370, 371, 372, 373, 374, 375, 376, 377, 378, 380,
                     381, 382, 385, 386, 387, 389, 39, 40, 41, 420, 421, 423,
                     43, 44, 45, 46, 47, 48, 49, 500, 501, 502, 503, 504,
                     505, 506, 507, 508, 509, 51, 52, 53, 54, 55, 56, 57, 58,
                     590, 591, 592, 593, 595, 597, 598, 599, 60, 61, 62, 63,
                     64, 65, 66, 670, 672, 673, 674, 675, 676, 677, 678, 679,
                     680, 681, 682, 683, 685, 686, 687, 688, 689, 690, 691,
                     692, 7, 81, 82, 84, 850, 852, 853, 855, 856, 86, 870,
                     880, 886, 90, 91, 92, 93, 94, 95, 960, 961, 962, 963,
                     964, 965, 966, 967, 968, 970, 971, 972, 973, 974, 975,
                     976, 977, 98, 992, 993, 994, 995, 996, 998]


def count_unknown_sms():
    from dispatcher.models import HotlineEvent
    return HotlineEvent.objects.filter(processed=False,
                                       event_type=HotlineEvent.TYPE_SMS_UNKNOWN).count()


def count_unarchived_sms():
    from dispatcher.models import HotlineEvent
    return HotlineEvent.objects.filter(processed=True, answer__isnull=True).count()


def count_unprocessed():
    from dispatcher.models import HotlineEvent
    return HotlineEvent.objects.filter(processed=False,
                                       event_type__in=HotlineEvent.HOTLINE_TYPES).count()


def is_valid_number(number):
    ''' checks if number is valid for HOTLINE_NUMBERS

        We want to get rid of operator spam '''
    if number is None:
        return False
    indicator, clean_number = clean_phone_number(number)
    return len(clean_number) >= NB_CHARS_VALID_NUMBER


def number_is_blacklisted(number):
    from dispatcher.models import BlackList
    identity = join_phone_number(*clean_phone_number(number))
    if BlackList.objects.filter(identity=identity).count():
        b = BlackList.objects.get(identity=identity)
        b.call_count += 1
        b.save()
        return True
    else:
        return False


def phone_number_is_int(number):
    ''' whether number is in international format '''
    if re.match(r'^[+|(]', number):
        return True
    if re.match(r'^\d{1,4}\.\d+$', number):
        return True
    return False


def get_phone_number_indicator(number):
    ''' extract indicator from number or "" '''
    for indic in ALL_COUNTRY_CODES:
        if number.startswith("%s" % indic) or number.startswith("+%s" % indic):
            return str(indic)
    return ""


def clean_phone_number(number):
    ''' return (indicator, number) cleaned of space and other '''
    # clean up
    if not isinstance(number, basestring):
        number = number.__str__()

    # cleanup markup
    clean_number = re.sub(r'[^\d\+]', '', number)

    if phone_number_is_int(clean_number):
        h, indicator, clean_number = \
            clean_number.partition(get_phone_number_indicator(clean_number))
        return (indicator, clean_number)

    return (None, clean_number)


def join_phone_number(prefix, number, force_intl=True):
    if not prefix and force_intl:
        prefix = COUNTRY_PREFIX
    return '+%s%s' % (prefix, number)


def operator_from_mali_number(number, default=ORANGE):
    ''' ORANGE or MALITEL based on the number prefix '''

    indicator, clean_number = clean_phone_number(number)
    if indicator is not None and indicator != str(COUNTRY_PREFIX):
        return FOREIGN

    malitel_prefixes = [2, 6, 98, 99]
    orange_prefixes = [7, 9, 4, 8, 90, 91]

    for prefix in malitel_prefixes:
        if clean_number.startswith(str(prefix)):
            return MALITEL

    for prefix in orange_prefixes:
        if clean_number.startswith(str(prefix)):
            return ORANGE

    return default


def all_hotline_numbers(operator=None):
    ''' Hotline numbers (used by public)

        If operator is passed, restrict results to it '''

    if not operator is None:
        return settings.HOTLINE_NUMBERS.get(operator, [])

    numbers = []
    for operator_numbers in settings.HOTLINE_NUMBERS:
        numbers += operator_numbers
    return numbers


def all_volunteers_numbers(operator=None):
    ''' Volunteers numbers (non public)

        If operator is passed, restrict results to it '''

    if not operator is None:
        return settings.HOTLINE_VOLUNTEERS_NUMBERS.get(operator, [])

    numbers = []
    for operator_numbers in settings.HOTLINE_VOLUNTEERS_NUMBERS.values():
        numbers += operator_numbers
    return numbers


def clean_phone_number_str(number):
    ''' properly formated for visualization: (xxx) xx xx xx xx '''

    def format(number):
        if len(number) % 2 == 0:
            span = 2
        else:
            span = 3
        # use NBSP
        return " ".join(["".join(number[i:i + span])
                        for i in range(0, len(number), span)])

    indicator, clean_number = clean_phone_number(number)
    if indicator:
        return "(%(ind)s) %(num)s" \
               % {'ind': indicator,
                  'num': format(clean_number)}
    return format(clean_number)


def make_ushahidi_request(event):

    params = {'from': event.identity,
              'message': event.sms_message,
              'message_id': event.id,
              'sent_to': event.hotline_number,
              'secret': settings.USHAHIDI_SECRET,
              'sent_timestamp': int(to_timestamp(event.received_on) * 1000)}

    req = requests.get(settings.USHAHIDI_URL, params=params)

    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError:
        return False

    response = json.loads(req.text)
    if response.get('payload', {}).get('success', False) in (True, "true"):
        event.processed = True
        event.save()
        return True
    return False


def send_email(recipients, message=None, template=None, context={},
               title=None, title_template=None, sender=None):
    """ forge and send an email message

        recipients: a list of or a string email address
        message: string or template name to build email body
        title: string or title_template to build email subject
        sender: string otherwise EMAIL_SENDER setting
        content: a dict to be used to render both templates

        returns: (success, message)
            success: a boolean if connecion went through
            message: an int number of email sent if success is True
                     else, an Exception """

    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]

    # remove empty emails from list
    # might happen everytime a user did not set email address.
    try:
        while True:
            recipients.remove(u"")
    except ValueError:
        pass

    # no need to continue if there's no recipients
    if recipients.__len__() == 0:
        return (False, ValueError("No Recipients for that message"))

    # no body text forbidden. most likely an error
    if not message and not template:
        return (False, ValueError("Unable to send empty email messages"))

    # build email body. rendered template has priority
    if template:
        email_msg = loader.get_template(template).render(Context(context))
    else:
        email_msg = message

    # if no title provided, use default one. empty title allowed
    if title is None and not title_template:
        email_subject = "Message from %(site)s" \
                        % {'site': Site.objects.get_current().name}

    # build email subject. rendered template has priority
    if title_template:
        email_subject = loader.get_template(title_template) \
                              .render(Context(context))
    elif title is not None:
        email_subject = title

    # title can't contain new line
    email_subject = email_subject.strip()

    # default sender from config
    if not sender:
        sender = settings.EMAIL_SENDER

    msgs = []
    for recipient in recipients:
        msgs.append((email_subject, email_msg, sender, [recipient]))

    try:
        mail.send_mass_mail(tuple(msgs), fail_silently=False)
        return (True, recipients.__len__())
    except smtplib.SMTPException as e:
        # log that error
        return (False, e)


def send_notification(event):

    if event.processed:
        return False

    title = "[HOTLINE SOS] Nouveau %s" % event.event_type
    message = ("Nouvel événnement sur la Hotline SOS:\n"
               "Date: %(date)s\n"
               "Numéro: %(num)s\n"
               "Type: %(type)s\n"
               "Message si SMS: %(sms)s\n\n"
               "Merci, SOS!\n\n%(url)s"
               % {'date': event.received_on,
                  'num': clean_phone_number_str(event.identity),
                  'type': event.event_type,
                  'sms': event.sms_message or "",
                  'url': "http://%s/" % Site.objects.get_current()})

    succ, msg = send_email(recipients=settings.NOTIFICATIONS_RECIPIENTS,
                           message=message, title=title)
    return succ


def operators():
    return settings.HOTLINE_NUMBERS.keys()


def datetime_range(start, stop=None, days=1):
    ''' return a list of dates incremented by 'days'

        start/stop = date or datetime
        days = increment number of days '''

    # stop at 00h00 today so we don't have an extra
    # point for today if the last period ends today.
    stop = stop or datetime.datetime(*datetime.date.today().timetuple()[:-4])

    while(start < stop):
        yield start
        start += datetime.timedelta(days)

    yield stop


def export_reponses(filename, with_private_data=False):
    ''' export the csv file '''
    from dispatcher.models import HotlineResponse, Topics

    name_col = lambda topic: "topic_{slug}".format(slug=topic.slug)

    topics = Topics.objects.order_by('slug')
    headers = ["received_on",
               "operator",
               "volunteer",
               "event_type",
               "response_date",
               "age",
               "sex",
               "duration",
               "location",
               "location_slug",
               "location_type",
               "topics_list",
               "topics_count"] + [name_col(topic) for topic in topics]

    if with_private_data:
        headers = ["identity"] + headers

    csv_file = open(filename, 'w')
    csv_writer = unicodecsv.DictWriter(csv_file, headers, encoding='utf-8')
    csv_writer.writeheader()

    for response in HotlineResponse.objects.all():

        data = {"received_on": response.request.received_on.isoformat(),
                "operator": response.request.operator,
                "volunteer": response.request.volunteer.username,
                "event_type": response.request.event_type,
                "response_date": response.response_date.isoformat(),
                "age": response.age,
                "sex": response.sex,
                "duration": int(response.duration),
                "location": response.location,
                "location_slug": getattr(response.location, 'slug', None),
                "location_type": getattr(response.location, 'type', None),
                "topics_list": ", ".join([topic.get('slug', '')
                                          for topic in response.topics.values()]),
                "topics_count": response.topics.count()}
        for topic in topics:
            data.update({name_col(topic): "true" if topic in response.topics.all() else None})

        if with_private_data:
            data.update({"identity": response.request.identity})

        csv_writer.writerow(data)

    csv_file.close()

    return filename


def zip_csv_reponses(filepath=None, with_private_data=False):
    ''' compress and export the csv file '''

    from dispatcher.models import Topics

    date_export = datetime.datetime.now()

    csv_filepath = "{}.csv".format(filepath.rsplit('.', 1)[0])
    zip_filepath = "{}.zip".format(filepath.rsplit('.', 1)[0])
    csv_filename = os.path.split(csv_filepath)[-1]

    # Export csv file
    export_reponses(csv_filepath, with_private_data=with_private_data)

    context = {'created_on': date_export,
               'topics': Topics.objects.all().order_by('slug')}

    readme_content = loader.get_template('datapackage.json').render(Context(context))

    zf = zipfile.ZipFile(zip_filepath, mode='w')

    readme_file = open('datapackage.json', "w")
    readme_file.write(readme_content.encode('utf-8'))
    readme_file.close()

    zf.write(csv_filepath, csv_filename)
    zf.write(readme_file.name)

    os.remove(csv_filepath)
    os.remove(readme_file.name)

    return zip_filepath


def get_default_context(page=''):
    return {'page': page,
            'nbarchive': count_unarchived_sms(),
            'nbunprocessed': count_unprocessed(),
            'nbsms': count_unknown_sms()}
