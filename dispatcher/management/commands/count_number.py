#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.core.management.base import BaseCommand

from dispatcher.models import HotlineEvent
from dispatcher.utils import operators, clean_phone_number


class Command(BaseCommand):
    help = "Update operator"

    def handle(self, *args, **kwargs):
        count_ext = 0
        for identity in HotlineEvent.objects.values('identity').distinct():
            indicator, number = clean_phone_number(identity.get('identity'))
            if indicator != '223':
                count_ext += 1

        count = [(operator, HotlineEvent.objects.filter(operator=operator)
                                                .values('identity').distinct()
                                                .count())
                  for operator in operators()] + [("Exterieur", count_ext)],
        for operator, opcount in count[0]:
            print(operator)
            print(opcount)