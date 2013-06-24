#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django import template
from django.template.defaultfilters import stringfilter

from dispatcher.utils import clean_phone_number_str

register = template.Library()


@register.filter(name='phone')
@stringfilter
def phone_number_formatter(number):
    ''' format phone number properly for display '''
    return clean_phone_number_str(number) #.replace(" ", " ")
