# -*- coding: utf-8 -*-

from django.views.decorators.cache import cache_page
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.utils import simplejson
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.template import RequestContext, loader
from django.contrib import messages
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator

from superview.views import SuperView as View

class GenericView(View):
    """ Generic view with some util methods. """

    def required_role(self, project, user, roles):
        try:
            purobj = ProjectUserRole.objects.get(
                user = user,
                project = project,
            )
        except ProjectUserRole.DoesNotExist:
            pass

    def render_to_ok(self, context={}):
        response = {'valid': True, 'errors': []}
        response.update(context)
        return self.render_json(response, ok=True)

    def render_to_error(self, context):
        response = {'valid': False, 'errors': []}
        response.update(context)
        return self.render_json(response, ok=False)
