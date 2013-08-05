#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.core.management.base import BaseCommand

from dispatcher.models import ResponseSMS, HotlineEvent


class Command(BaseCommand):
    help = "Response SMS"

    def handle(self, *args, **kwargs):
        message = ("Sos Democratie vous remercie pour votre participation "
                   "massive au scrutin du 1er tour. Restons mobilises pour le "
                   "retrait des cartes NINA et le 2eme tour. Conservons ce climat "
                   "apaise et democratique. Vive le Mali nouveau, uni, "
                   "pacifie, sur la voie d'un developpement durable.")
        for identity in HotlineEvent.objects.values('identity').distinct():
            try:
                existing = ResponseSMS.objects.get(identity=identity.get('identity'))
            except ResponseSMS.DoesNotExist:
                existing = None

            if not existing:
                sms = ResponseSMS.objects.create(identity=identity.get('identity'),
                                                 text=message)
                print(identity.get('identity'))
