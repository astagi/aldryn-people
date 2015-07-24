# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from parler.admin import TranslatableAdmin
from aldryn_translation_tools.admin import AllTranslationsMixin

from .models import Person, Group
from .forms import PersonForm


class PersonAdmin(AllTranslationsMixin, TranslatableAdmin):

    list_display = [
        '__str__', 'email', 'vcard_enabled', ]
    list_filter = ['groups', 'vcard_enabled']
    search_fields = ('translations__name', 'email', 'translations__function')
    raw_id_fields = ('user',)

    def get_prepopulated_fields(self, request, obj=None):
        # Using method since these are translated fields
        return {
            'slug': ('name',)
        }

    fieldsets = (
        (None, {
            'fields': (
                ('name', 'slug', ),
                'function', 'description',
            ),
        }),
        (_('Contact (untranslated)'), {
            'fields': (
                'visual', 'phone', 'mobile', 'fax', 'email', 'website',
                'user', 'vcard_enabled'
            ),
        }),
        (None, {
            'fields': (
                'groups',
            ),
        }),
    )

    form = PersonForm


class GroupAdmin(AllTranslationsMixin, TranslatableAdmin):

    list_display = ['__str__', 'city', ]
    search_filter = ['translations__name']
    fieldsets = (
        (None, {
            'fields': (
                ('name', 'slug', ),
                'description',
            ),
        }),
        (_('Contact (untranslated)'), {
            'fields': (
                'phone', 'fax', 'email', 'website',
                'address', 'postal_code', 'city'
            )
        }),
    )


admin.site.register(Person, PersonAdmin)
admin.site.register(Group, GroupAdmin)
