from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)


class IsStaffOrReadOnly(IsAuthenticatedOrReadOnly):

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.method in SAFE_METHODS:
                return True
            return (request.user.is_authenticated and request.user.is_staff)
        return False


class IsStaffOrCreateOnly(IsAuthenticated):

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.method == 'POST':
                return True
            return (request.user.is_authenticated and request.user.is_staff)
        return False


class IsAdmin(IsAuthenticated):

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return request.user.is_staff
        return False
