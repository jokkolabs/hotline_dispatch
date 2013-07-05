from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dispatcher.views.dashboard', name='home'),
    url(r'^sms$', 'dispatcher.views.sms_check', name='sms'),
    url(r'^sms/(?P<event_filter>[A-Z\_]+)$', 'dispatcher.views.sms_check', name='sms_filter'),
    url(r'^sms/(?P<event_id>[0-9]+)/(?P<new_type>[A-Za-z\_]+)/(?P<return_to>[A-Z\_]+)$', 'dispatcher.views.sms_change_type', name='sms_change_type'),

    url(r'^smssync$', 'dispatcher.views.smssync', name='smssync'),
    url(r'^ringsync$', 'dispatcher.views.ringsync_status', name='ringsync_status'),
    url(r'^ringsync/(?P<call_number>[\+a-z0-9A-Z\-\.\_]+)/(?P<call_timestamp>[0-9]+)/?$', 'dispatcher.views.ringsync', name='ringsync'),

    url(r'^password/?$', 'dispatcher.views.change_password', name='changepwd'),

    url(r'^data-entry$', 'dispatcher.views.data_entry', name='data_entry'),

    url(r'^blacklist$', 'dispatcher.views.blacklist', name='blacklist'),

    url(r'^status$', 'dispatcher.views.status', name='status'),
    url(r'^graph_data/$', 'dispatcher.views.graph_data', name='graph_data'),

    url(r'^entities/(?P<parent_slug>\d{8})/?$', 'dispatcher.views.entities_api', name='entities'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
)
