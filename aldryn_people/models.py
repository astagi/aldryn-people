# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
import six
from aldryn_people.vcard import Vcard

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse
import warnings

import reversion

from reversion.revisions import RegistrationError
from distutils.version import LooseVersion
from django import get_version
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _, override, force_text
from six import text_type

from aldryn_common.admin_fields.sortedm2m import SortedM2MModelField
from aldryn_translation_tools.models import (
    TranslatedAutoSlugifyMixin,
    TranslationHelperMixin,
)
from cms.models.pluginmodel import CMSPlugin
from cms.utils.i18n import get_current_language, get_default_language
from djangocms_text_ckeditor.fields import HTMLField
from filer.fields.image import FilerImageField
from parler.models import TranslatableModel, TranslatedFields
from aldryn_reversion.core import version_controlled_content


from .utils import get_additional_styles

# NOTE: We use LooseVersion and not StrictVersion because sometimes Aldryn uses
# patched build with version numbers of the form X.Y.Z.postN.
loose_version = LooseVersion(get_version())

if loose_version < LooseVersion('1.7.0'):
    # Prior to 1.7 it is pretty straight forward
    user_model = get_user_model()
    revision_manager = reversion.default_revision_manager
    if user_model not in revision_manager.get_registered_models():
        reversion.register(user_model)
else:
    # otherwise it is a pain, but thanks to solution of getting model from
    # https://github.com/django-oscar/django-oscar/commit/c479a1
    # we can do almost the same thing from the different side.
    from django.apps import apps
    from django.apps.config import MODELS_MODULE_NAME
    from django.core.exceptions import AppRegistryNotReady

    def get_model(app_label, model_name):
        """
        Fetches a Django model using the app registry.
        This doesn't require that an app with the given app label exists,
        which makes it safe to call when the registry is being populated.
        All other methods to access models might raise an exception about the
        registry not being ready yet.
        Raises LookupError if model isn't found.
        """
        try:
            return apps.get_model(app_label, model_name)
        except AppRegistryNotReady:
            if apps.apps_ready and not apps.models_ready:
                # If this function is called while `apps.populate()` is
                # loading models, ensure that the module that defines the
                # target model has been imported and try looking the model up
                # in the app registry. This effectively emulates
                # `from path.to.app.models import Model` where we use
                # `Model = get_model('app', 'Model')` instead.
                app_config = apps.get_app_config(app_label)
                # `app_config.import_models()` cannot be used here because it
                # would interfere with `apps.populate()`.
                import_module('%s.%s' % (app_config.name, MODELS_MODULE_NAME))
                # In order to account for case-insensitivity of model_name,
                # look up the model through a private API of the app registry.
                return apps.get_registered_model(app_label, model_name)
            else:
                # This must be a different case (e.g. the model really doesn't
                # exist). We just re-raise the exception.
                raise

    # now get the real user model
    user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
    model_app_name, model_model = user_model.split('.')
    user_model_object = get_model(model_app_name, model_model)
    # and try to register, if we have a registration error - that means that
    # it has been registered already
    try:
        reversion.register(user_model_object)
    except RegistrationError:
        pass


@version_controlled_content
@python_2_unicode_compatible
class Group(TranslationHelperMixin, TranslatedAutoSlugifyMixin,
            TranslatableModel):
    slug_source_field_name = 'name'
    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=255,
                              help_text=_("Provide this group's name.")),
        description=HTMLField(_('description'), blank=True),
        slug=models.SlugField(_('slug'), max_length=255, default='',
            blank=True,
            help_text=_("Leave blank to auto-generate a unique slug.")),
    )
    address = models.TextField(
        verbose_name=_('address'), blank=True)
    postal_code = models.CharField(
        verbose_name=_('postal code'), max_length=20, blank=True)
    city = models.CharField(
        verbose_name=_('city'), max_length=255, blank=True)
    phone = models.CharField(
        verbose_name=_('phone'), null=True, blank=True, max_length=100)
    fax = models.CharField(
        verbose_name=_('fax'), null=True, blank=True, max_length=100)
    email = models.EmailField(
        verbose_name=_('email'), blank=True, default='')
    website = models.URLField(
        verbose_name=_('website'), null=True, blank=True)

    @property
    def company_name(self):
        warnings.warn(
            '"Group.company_name" has been refactored to "Group.name"',
            DeprecationWarning
        )
        return self.safe_translation_getter('name')

    @property
    def company_description(self):
        warnings.warn(
            '"Group.company_description" has been refactored to '
            '"Group.description"',
            DeprecationWarning
        )
        return self.safe_translation_getter('description')

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    def __str__(self):
        return self.safe_translation_getter(
            'name', default=_('Group: {0}').format(self.pk))

    def get_absolute_url(self, language=None):
        if not language:
            language = get_current_language() or get_default_language()
        slug, language = self.known_translation_getter(
            'slug', None, language_code=language)
        if slug:
            kwargs = {'slug': slug}
        else:
            kwargs = {'pk': self.pk}
        with override(language):
            return reverse('aldryn_people:group-detail', kwargs=kwargs)


@version_controlled_content(follow=['groups', 'user'])
@python_2_unicode_compatible
class Person(TranslationHelperMixin, TranslatedAutoSlugifyMixin,
             TranslatableModel):
    slug_source_field_name = 'name'

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=255, blank=False,
            default='', help_text=_("Provide this person's name.")),
        slug=models.SlugField(_('unique slug'), max_length=255, blank=True,
            default='',
            help_text=_("Leave blank to auto-generate a unique slug.")),
        function=models.CharField(_('role'),
            max_length=255, blank=True, default=''),
        description=HTMLField(_('description'),
            blank=True, default='')
    )
    phone = models.CharField(
        verbose_name=_('phone'), null=True, blank=True, max_length=100)
    mobile = models.CharField(
        verbose_name=_('mobile'), null=True, blank=True, max_length=100)
    fax = models.CharField(
        verbose_name=_('fax'), null=True, blank=True, max_length=100)
    email = models.EmailField(
        verbose_name=_("email"), blank=True, default='')
    website = models.URLField(
        verbose_name=_('website'), null=True, blank=True)
    groups = SortedM2MModelField(
        'aldryn_people.Group', default=None, blank=True, related_name='people',
        help_text=_('Choose and order the groups for this person, the first '
                    'will be the "primary group".'))
    visual = FilerImageField(
        null=True, blank=True, default=None, on_delete=models.SET_NULL)
    vcard_enabled = models.BooleanField(
        verbose_name=_('enable vCard download'), default=True)
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        null=True, blank=True, unique=True, related_name='persons')

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('People')

    def __str__(self):
        pkstr = str(self.pk)

        if six.PY2:
            pkstr = six.u(pkstr)
        name = self.name.strip()
        return name if len(name) > 0 else pkstr

    @property
    def primary_group(self):
        """Simply returns the first in `groups`, if any, else None."""
        return self.groups.first()

    @property
    def comment(self):
        return self.safe_translation_getter('description', '')

    def get_absolute_url(self, language=None):
        if not language:
            language = get_current_language()
        slug, language = self.known_translation_getter(
            'slug', None, language_code=language)
        if slug:
            kwargs = {'slug': slug}
        else:
            kwargs = {'pk': self.pk}
        with override(language):
            return reverse('aldryn_people:person-detail', kwargs=kwargs)

    def get_vcard_url(self, language=None):
        if not language:
            language = get_current_language()
        slug = self.safe_translation_getter(
            'slug', None, language_code=language, any_language=False)
        if slug:
            kwargs = {'slug': slug}
        else:
            kwargs = {'pk': self.pk}
        with override(language):
            return reverse('aldryn_people:download_vcard', kwargs=kwargs)

    def get_vcard(self, request=None):
        vcard = Vcard()
        function = self.safe_translation_getter('function')

        safe_name = self.safe_translation_getter(
            'name', default="Person: {0}".format(self.pk))
        vcard.add_line('FN', safe_name)
        vcard.add_line('N', [None, safe_name, None, None, None])

        if self.visual:
            ext = self.visual.extension.upper()
            try:
                with open(self.visual.path, 'rb') as f:
                    data = force_text(base64.b64encode(f.read()))
                    vcard.add_line('PHOTO', data, TYPE=ext, ENCODING='b')
            except IOError:
                if request:
                    url = urlparse.urljoin(request.build_absolute_uri(),
                                           self.visual.url),
                    vcard.add_line('PHOTO', url, TYPE=ext)

        if self.email:
            vcard.add_line('EMAIL', self.email)

        if function:
            vcard.add_line('TITLE', self.function)

        if self.phone:
            vcard.add_line('TEL', self.phone, TYPE='WORK')
        if self.mobile:
            vcard.add_line('TEL', self.mobile, TYPE='CELL')

        if self.fax:
            vcard.add_line('TEL', self.fax, TYPE='FAX')
        if self.website:
            vcard.add_line('URL', self.website)

        if self.primary_group:
            group_name = self.primary_group.safe_translation_getter(
                'name', default="Group: {0}".format(self.primary_group.pk))
            if group_name:
                vcard.add_line('ORG', group_name)
            if (self.primary_group.address or self.primary_group.city or
                    self.primary_group.postal_code):
                vcard.add_line('ADR', (
                    None, None,
                    self.primary_group.address,
                    self.primary_group.city,
                    None,
                    self.primary_group.postal_code,
                    None,
                ), TYPE='WORK')

            if self.primary_group.phone:
                vcard.add_line('TEL', self.primary_group.phone, TYPE='WORK')
            if self.primary_group.fax:
                vcard.add_line('TEL', self.primary_group.fax, TYPE='FAX')
            if self.primary_group.website:
                vcard.add_line('URL', self.primary_group.website)

        return str(vcard)


@python_2_unicode_compatible
class BasePeoplePlugin(CMSPlugin):

    STYLE_CHOICES = [
        ('standard', _('Standard')),
        ('feature', _('Feature'))
    ] + get_additional_styles()

    style = models.CharField(
        _('Style'), choices=STYLE_CHOICES,
        default=STYLE_CHOICES[0][0], max_length=50)

    people = SortedM2MModelField(
        Person, blank=True, null=True,
        help_text=_('Select and arrange specific people, or, leave blank to '
                    'select all.')
    )

    class Meta:
        abstract = True

    def copy_relations(self, oldinstance):
        self.people = oldinstance.people.all()

    def get_selected_people(self):
        return self.people.select_related('visual')

    def __str__(self):
        return text_type(self.pk)


class PeoplePlugin(BasePeoplePlugin):

    group_by_group = models.BooleanField(
        verbose_name=_('group by group'),
        default=True,
        help_text=_('Group people by their group.')
    )
    show_ungrouped = models.BooleanField(
        verbose_name=_('show ungrouped'),
        default=False,
        help_text=_('When using "group by group", show ungrouped people too.')
    )
    show_links = models.BooleanField(
        verbose_name=_('Show links to Detail Page'), default=False)
    show_vcard = models.BooleanField(
        verbose_name=_('Show links to download vCard'), default=False)

    class Meta:
        abstract = False
