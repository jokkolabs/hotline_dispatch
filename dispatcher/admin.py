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
        (None, {'fields': ('email', 'password', 'first_name', 'last_name',
                           'is_superuser', 'is_staff', 'is_active',
                           'operator', 'phone_number')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name',
                       'is_superuser', 'is_staff', 'is_active', 'operator')}),
    )


admin.site.register(HotlineVolunteer, CustomUserAdmin)
admin.site.register(HotlineEvent)
admin.site.register(HotlineResponse)
admin.site.register(Entity)
admin.site.register(BlackList)
admin.site.register(Topics)
