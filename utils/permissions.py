# -*- coding: utf-8 -*-

from rest_framework.permissions import BasePermission
from django.conf import settings

class IsAuthenticatedOrDevMode(BasePermission):
    def has_permission(self, request, view):
        if settings.DEV_MODE:
            return True
        return request.user and request.user.is_authenticated