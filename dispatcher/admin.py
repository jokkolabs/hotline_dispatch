#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

from dispatcher.models import (HotlineEvent, HotlineVolunteer,
                               HotlineResponse, Entity, BlackList, Topics)


class UserModificationForm(forms.ModelForm):
    class Meta:
        model = HotlineVolunteer


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = HotlineVolunteer
        fields = ('email',)

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomUserAdmin(UserAdmin):
    form = UserModificationForm
    add_form = UserCreationForm
    list_display = ("username", "first_name", "last_name", "operator")
    ordering = ("username",)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'first_name', 'last_name',
                           'is_superuser', 'is_staff', 'is_active',
                           'operator', 'phone_number')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'first_name', 'last_name',
                       'is_superuser', 'is_staff', 'is_active', 'operator')}),
    )


class CustomHotlineEvent(admin.ModelAdmin):
    list_display = ("received_on", "operator", "identity", "event_type",
                    "sms_message", "created_on",  "processed", "volunteer", "answer")
    list_filter = ("created_on", "event_type", "operator", "volunteer")


class CustomHotlineResponse(admin.ModelAdmin):
    list_display = ("response_date", "created_on", "age", "sex",
                    "duration", "location",)
    list_filter = ("created_on", "sex",)


class CustomEntity(admin.ModelAdmin):
    list_display = ("slug", "name", "type", "latitude",
                    "longitude", "parent",)


class CustomTopics(admin.ModelAdmin):
    list_display = ("slug", "name", "category",)
    list_filter = ("category",)


class CustomBlackList(admin.ModelAdmin):
    list_display = ("identity", "call_count",)


admin.site.register(HotlineVolunteer, CustomUserAdmin)
admin.site.register(HotlineEvent, CustomHotlineEvent)
admin.site.register(HotlineResponse, CustomHotlineResponse)
admin.site.register(Entity, CustomEntity)
admin.site.register(BlackList, CustomBlackList)
admin.site.register(Topics, CustomTopics)
