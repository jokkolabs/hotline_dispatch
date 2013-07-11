#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.core.management.base import BaseCommand

from dispatcher.models import HotlineEvent
from dispatcher.utils import operator_from_mali_number


class Command(BaseCommand):
    help = "Update operator"

    def handle(self, *args, **kwargs):

        for event in HotlineEvent.objects.all():
            print(event.identity)
            event.operator = operator_from_mali_number(event.identity)
            event.save()

        print("End of Updated.")
