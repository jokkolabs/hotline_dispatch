#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import csv
import codecs
import cStringIO

from django.core.management.base import BaseCommand

from dispatcher.models import Entity


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class Command(BaseCommand):
    help = "Import Entities from raw CSV"

    def handle(self, *args, **kwargs):

        def fid(anid):
            return '%s%s' % (anid, ''.join(['0' for x in xrange(8 - len(anid))]))

        def clean(name):
            return name.strip().upper()

        region_names = {
            1: "Kayes",
            2: "Koulikoro",
            3: "Sikasso",
            4: "Ségou",
            5: "Mopti",
            6: "Tombouctou",
            7: "Gao",
            8: "Kidal",
            9: "Bamako"
        }

        file_io = open('villages_mali.csv', 'r')
        reader = UnicodeReader(file_io)
        first = True

        Entity.objects.all().delete()
        print("All Entities removed.")

        for codec, cercle98, commune, cheflieu, nom1, lon98, lat98 in reader:
            if first:
                first = False
                continue

            id_region = fid(codec[:1])
            id_cercle = fid(codec[:2])
            id_commune = fid(codec[:5])

            if not Entity.objects.filter(slug=id_region).count():
                Entity.objects.create(slug=id_region,
                                      name=clean(region_names.get(int(codec[:1]))),
                                      type=Entity.TYPE_REGION)

            if not Entity.objects.filter(slug=id_cercle).count():
                Entity.objects.create(slug=id_cercle,
                                      name=clean(cercle98),
                                      type=Entity.TYPE_CERCLE,
                                      parent=Entity.objects.get(slug=id_region))

            if not Entity.objects.filter(slug=id_commune).count():
                Entity.objects.create(slug=id_commune,
                                      name=clean(commune),
                                      type=Entity.TYPE_COMMUNE,
                                      parent=Entity.objects.get(slug=id_cercle))

            # if entity with ID exists, it's a typo in the source
            # and we bump ID by one
            while True:
                if Entity.objects.filter(slug=codec).count():
                    codec = int(codec) + 1
                else:
                    break

            entity = Entity.objects.create(slug=codec,
                                           name=clean(nom1),
                                           type=Entity.TYPE_VILLAGE,
                                           latitude=float(lat98) or None,
                                           longitude=float(lon98) or None,
                                           parent=Entity.objects.get(slug=id_commune))

            print(entity)

        file_io.close()

        print("Entities created")
