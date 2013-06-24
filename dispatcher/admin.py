#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.contrib import admin

from dispatcher.models import (HotlineEvent, HotlineVolunteer,
                               HotlineResponse, Entity, BlackList, Topics)

admin.site.register(HotlineEvent)
admin.site.register(HotlineVolunteer)
admin.site.register(HotlineResponse)
admin.site.register(Entity)
admin.site.register(BlackList)
admin.site.register(Topics)
