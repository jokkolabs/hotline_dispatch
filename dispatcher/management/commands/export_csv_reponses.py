#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.core.management.base import BaseCommand

from dispatcher.utils import export_reponses


class Command(BaseCommand):
    help = "Export Responses in CSV"

    def handle(self, csv_file, *args, **kwargs):

        export_reponses(csv_file)

        print("Fin.")
