#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dispatcher.views.dashboard', name='home'),
    url(r'^sms$', 'dispatcher.views.sms_check', name='sms'),
    url(r'^sms/(?P<event_filter>[A-Z\_]+)$', 'dispatcher.views.sms_check', name='sms_filter'),
    url(r'^sms/(?P<event_id>[0-9]+)/(?P<new_type>[A-Za-z\_]+)/(?P<return_to>[A-Z\_]+)$', 'dispatcher.views.sms_change_type', name='sms_change_type'),

     # # Android API
    url(r'^fondasms/?$', 'fondasms.views.fondasms_handler',
        {'handler_module': 'dispatcher.fondasms_handlers',
         'send_automatic_reply': True,
         'automatic_reply_via_handler': False,
         'automatic_reply_text': ("Merci de votre appel. La Hotline "
                                  "SOS Démocratie vous rappelle bientôt.")},
        name='fondasms'),
    url(r'^tester/?$', 'fondasms.views.fondasms_tester',
        name='fondasms_tester'),

    # url(r'^smssync$', 'dispatcher.views.smssync', name='smssync'),
    # url(r'^ringsync$', 'dispatcher.views.ringsync_status', name='ringsync_status'),
    # url(r'^ringsync/(?P<call_number>[\+a-z0-9A-Z\-\.\_]+)/(?P<call_timestamp>[0-9]+)/?$',
    #     'dispatcher.views.ringsync', name='ringsync'),

    url(r'^password/?$', 'dispatcher.views.change_password', name='changepwd'),

    url(r'^data-entry$', 'dispatcher.views.data_entry', name='data_entry'),

    url(r'^blacklist$', 'dispatcher.views.blacklist', name='blacklist'),

    url(r'^status$', 'dispatcher.views.status', name='status'),
    url(r'^export$', 'dispatcher.views.exported_status', name='export'),
    url(r'^graph_data/$', 'dispatcher.views.graph_data', name='graph_data'),

    url(r'^entities/(?P<parent_slug>\d{8})/?$', 'dispatcher.views.entities_api', name='entities'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
)
