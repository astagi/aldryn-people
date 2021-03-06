# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import django

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://localhost:9001/solr/default',
        'TIMEOUT': 60 * 5,
        'INCLUDE_SPELLING': True,
        'BATCH_SIZE': 100,
        'EXCLUDED_INDEXES': ['thirdpartyapp.search_indexes.BarIndex'],
    },
    'en': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://my-solr-server/solr/my-site-en/',
        'TIMEOUT': 60 * 5,
        'INCLUDE_SPELLING': True,
        'BATCH_SIZE': 100,
    },
    'de': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://my-solr-server/solr/my-site-de/',
        'TIMEOUT': 60 * 5,
        'INCLUDE_SPELLING': True,
        'BATCH_SIZE': 100,
    },
}

HELPER_SETTINGS = {
    # Use of this custom URLs provides a shortcut when testing apphooks
    'ROOT_URLCONF': 'aldryn_people.tests.urls',
    'TIME_ZONE': 'Europe/Zurich',
    'HAYSTACK_CONNECTIONS': HAYSTACK_CONNECTIONS,
    'INSTALLED_APPS': [
        'aldryn_apphook_reload',
        'aldryn_common',
        'aldryn_reversion',
        'aldryn_translation_tools',
        'djangocms_text_ckeditor',
        'easy_thumbnails',
        'filer',
        'parler',
        'reversion',
        'sortedm2m',
    ],
    'MIGRATION_MODULES': {
        'filer': 'filer.migrations_django',
    },
    'THUMBNAIL_PROCESSORS': (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    ),
    'ALDRYN_BOILERPLATE_NAME': 'bootstrap3',
    'LANGUAGES': (
        ('en', 'English'),
        ('de', 'German'),
        ('fr', 'French'),
    ),
    'CMS_LANGUAGES': {
        1: [
            {
                'code': 'de',
                'name': 'Deutsche',
                'fallbacks': ['en', ]  # FOR TESTING DO NOT ADD 'fr' HERE
            },
            {
                'code': 'fr',
                'name': 'Française',
                'fallbacks': ['en', ]  # FOR TESTING DO NOT ADD 'de' HERE
            },
            {
                'code': 'en',
                'name': 'English',
                'fallbacks': ['de', 'fr', ]
            },
            {
                'code': 'it',
                'name': 'Italiano',
                'fallbacks': ['fr', ]  # FOR TESTING, LEAVE AS ONLY 'fr'
            },
        ],
    },
    # app-specific
    'PARLER_LANGUAGES': {
        1: (
            {'code': 'de', },
            {'code': 'fr', },
            {'code': 'en', },
        ),
        'default': {
            'fallback': 'en',
            'hide_untranslated': True,  # PLEASE DO NOT CHANGE THIS
        }
    },
}

# This set of MW classes should work for Django 1.6 and 1.7.
MIDDLEWARE_CLASSES_16_17 = [
    'aldryn_apphook_reload.middleware.ApphookReloadMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware'
]

MIDDLEWARE_CLASSES_18 = [
    'aldryn_apphook_reload.middleware.ApphookReloadMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
]

# Use PEP 386-compliant version number
django_version = django.get_version()

if django_version.startswith('1.6.') or django_version.startswith('1.7.'):
    HELPER_SETTINGS['MIDDLEWARE_CLASSES'] = MIDDLEWARE_CLASSES_16_17
elif django_version.startswith('1.8.'):
    HELPER_SETTINGS['MIDDLEWARE_CLASSES'] = MIDDLEWARE_CLASSES_18


def run():
    from djangocms_helper import runner
    runner.cms('aldryn_people', extra_args=['--boilerplate'])

if __name__ == "__main__":
    run()
