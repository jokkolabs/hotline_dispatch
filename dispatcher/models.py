#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.db import models
from django.contrib.auth.models import AbstractUser

from dispatcher.utils import ORANGE, MALITEL

OPERATORS = ((ORANGE, ORANGE.capitalize()),
             (MALITEL, MALITEL.capitalize()))


class HotlineEvent(models.Model):

    class Meta:
        unique_together = [('identity', 'received_on')]

    TYPE_CALL_ME = 'CALL_ME'
    TYPE_CHARGE_ME = 'CHARGE_ME'
    TYPE_SMS_UNKNOWN = 'SMS_UNKNOWN'
    TYPE_SMS_USHAHIDI = 'SMS_USHAHIDI'
    TYPE_SMS_HOTLINE = 'SMS_HOTLINE'
    TYPE_RING = 'RING'
    TYPE_SMS_SPAM = 'SMS_SPAM'
    TYPES = ((TYPE_CALL_ME, "Peux-tu me rappler?"),
             (TYPE_CHARGE_ME, "Peux-tu recharger mon compte?"),
             (TYPE_RING, "Bip."),
             (TYPE_SMS_UNKNOWN, "SMS à déterminer."),
             (TYPE_SMS_HOTLINE, "SMS (Hotline)."),
             (TYPE_SMS_USHAHIDI, "SMS (Ushahidi)."),
             (TYPE_SMS_SPAM, "SMS (SPAM)"))
    HOTLINE_TYPES = (TYPE_CALL_ME, TYPE_CHARGE_ME, TYPE_SMS_HOTLINE, TYPE_RING)
    SMS_TYPES = (TYPE_SMS_UNKNOWN, TYPE_SMS_HOTLINE, TYPE_SMS_USHAHIDI, TYPE_SMS_SPAM)

    identity = models.CharField(max_length=30)
    event_type = models.CharField(max_length=50, choices=TYPES)
    received_on = models.DateTimeField()
    created_on = models.DateTimeField(auto_now_add=True)
    hotline_number = models.CharField(max_length=30, null=True, blank=True)
    sms_message = models.TextField(null=True, blank=True)
    processed = models.BooleanField(default=False)
    operator = models.CharField(max_length=50, choices=OPERATORS)

    def __unicode__(self):
        return "%(type)s/%(number)s" % {'type': self.event_type,
                                        'number': self.identity}


class HotlineVolunteer(AbstractUser):

    operator = models.CharField(max_length=50, choices=OPERATORS, null=True, blank=True)
    phone_number = models.CharField(max_length=30, null=True, blank=True)
