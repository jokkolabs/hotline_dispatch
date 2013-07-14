#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import datetime

from django.core.management.base import BaseCommand
from optparse import make_option

from dispatcher.utils import zip_csv_reponses, export_reponses


class Command(BaseCommand):
    help = "Export Responses in CSV or ZIPed CSV"
    option_list = BaseCommand.option_list + (
        make_option('-f', '--filename',
                    action="store",
                    dest='filename',
                    default=None,
                    help='Output file to write export to. Use .csv or .zip'),
        make_option('-F', '--full',
                    action="store_true",
                    dest='full',
                    default=False,
                    help='Whether to export data with personnal numbers'))

    def handle(self, *args, **options):

        datestr = datetime.datetime.now().strftime('%Y-%m-%d-%Hh%M')
        filename = options.get('filename')
        with_private_data = options.get('full', False)

        if filename is None:
            filename = "hotline_data_{date}.csv".format(date=datestr)

        if filename.endswith('.zip'):
            print(zip_csv_reponses(filename, with_private_data=with_private_data))
        else:
            print(export_reponses(filename, with_private_data=with_private_data))
