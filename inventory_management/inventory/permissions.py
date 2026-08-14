from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Categories/Products/Customers:
    - Any authenticated user may view (GET/HEAD/OPTIONS).
    - Only staff/admin users may create, update, or delete.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Invoices:
    - Any authenticated user may view invoices they can see (queryset already
      restricts non-staff users to their own invoices).
    - Only the invoice's creator or a staff/admin user may update/delete it.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user.is_staff or obj.created_by_id == request.user.id)
