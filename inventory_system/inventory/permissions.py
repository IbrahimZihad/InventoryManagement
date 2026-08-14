from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Any authenticated user can read (list/retrieve) Category and Product data.
    Only staff/admin users can create, update, or delete them.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Any authenticated user can create invoices and read invoices they can see.
    Only the invoice's own creator or an admin/staff user may update/delete it.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user.is_staff or obj.created_by_id == request.user.id)
