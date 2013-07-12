#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import json
import zipfile

from django.core.management.base import BaseCommand
from django.template import loader, Context

from dispatcher.views import get_status_context, get_graph_context


class Command(BaseCommand):
    help = "Export Stats in HTML and JSON"

    def handle(self, *args, **kwargs):

        html_filename = "hotline_stats.html"
        json_hotline_data = "hotline_data.json"
        json_graph_data = "graph_data.json"
        context = get_status_context()

        # generate HTML page
        html_content = loader.get_template("status_for_export.html").render(Context(context))
        myfile = open(html_filename, 'w')
        myfile.write(html_content.encode('utf-8'))
        myfile.close()

        # generate JSON file
        data_event = {'total_events': context.get('total_events'),
                      'last_event': context.get('last_event').received_on.isoformat()}
        hotline_data_fp = open(json_hotline_data, 'w')
        json.dump(data_event, hotline_data_fp)
        hotline_data_fp.close()

        # generate JSON file
        graph_data = get_graph_context()
        graph_data_fp = open(json_graph_data, 'w')
        json.dump(graph_data, graph_data_fp)
        graph_data_fp.close()

        # create ZIP archive
        static_dir = os.path.join('dispatcher', 'static')
        zf = zipfile.ZipFile('hotline_export.zip', mode='w')
        zf.write(html_filename)
        zf.write(json_hotline_data)
        zf.write(json_graph_data)
        for folder in os.listdir(static_dir):
            for asset in os.listdir(os.path.join(static_dir, folder)):
                zf.write(os.path.join(static_dir, folder, asset),
                         os.path.join('static', folder, asset))
        zf.close()

        os.remove(html_filename)
        os.remove(json_hotline_data)
        os.remove(json_graph_data)

        print("Fin.")
