from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class IsAdminOrPost(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['POST', 'GET', 'HEAD', 'OPTIONS']:
            return True
        return bool(request.user and request.user.is_staff)

class IsAdminOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['POST', 'GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']:
            return True
        return bool(request.user and request.user.is_staff)
