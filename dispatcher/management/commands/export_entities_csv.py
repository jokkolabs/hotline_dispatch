#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

import unicodecsv
from django.core.management.base import BaseCommand

from dispatcher.models import Entity

LEVELS = [Entity.TYPE_REGION, Entity.TYPE_CERCLE, Entity.TYPE_COMMUNE, Entity.TYPE_VILLAGE]


class Command(BaseCommand):
    help = "Export Entitites in CSV"

    def handle(self, *args, **options):

        headers = ['code', 'region', 'cercle', 'commune', 'vfq', 'gps', 'longitude', 'latitude', 'parent_code']

        file_io = open('mali-entities.csv', 'w')
        csv_writer = unicodecsv.DictWriter(file_io, headers, encoding='utf-8')
        csv_writer.writeheader()

        def data_from(entity):
            def get_level_name_from(entity, level):
                if entity.type == level:
                    return entity.name.encode('utf-8')

                ent_index = LEVELS.index(entity.type)
                target_index = LEVELS.index(level)

                if target_index > ent_index:
                    return None

                return entity.get_ancestors()[target_index].name.encode('utf-8')

            def get_geopoint(entity):
                if entity.latitude and entity.longitude:
                    return "{lon}, {lat}".format(lon=entity.longitude, lat=entity.latitude)
                return None

            return {'code': entity.slug,
                    'region': get_level_name_from(entity, entity.TYPE_REGION),
                    'cercle': get_level_name_from(entity, entity.TYPE_CERCLE),
                    'commune': get_level_name_from(entity, entity.TYPE_COMMUNE),
                    'vfq': get_level_name_from(entity, entity.TYPE_VILLAGE),
                    'gps': get_geopoint(entity),
                    'longitude': entity.longitude,
                    'latitude': entity.latitude,
                    'parent_code': getattr(entity.parent, 'slug', None)}

        count = 0

        for level in LEVELS:
            print(level)
            for entity in Entity.objects.filter(type=level):
                print("{} ({})".format(entity, entity.type))
                csv_writer.writerow(data_from(entity))
                count += 1
                # if count > 50:
                    # break
        file_io.close()
