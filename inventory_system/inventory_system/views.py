from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request, format=None):
    """
    GET /
    Public landing page for the API: lists the main endpoint groups so
    anyone hitting the root gets their bearings instead of a 404.
    """
    return Response(
        {
            "message": "Inventory Management System API",
            "docs": "See README.md for full endpoint reference and example payloads.",
            "auth": {
                "register": reverse("accounts:register", request=request, format=format),
                "login": reverse("accounts:login", request=request, format=format),
                "logout": reverse("accounts:logout", request=request, format=format),
                "token_obtain": reverse("accounts:token_obtain_pair", request=request, format=format),
                "token_refresh": reverse("accounts:token_refresh", request=request, format=format),
                "token_verify": reverse("accounts:token_verify", request=request, format=format),
            },
            "account": {
                "me": reverse("accounts:me", request=request, format=format),
                "change_password": reverse("accounts:change-password", request=request, format=format),
            },
            "inventory": {
                "categories": reverse("inventory:category-list", request=request, format=format),
                "customers": reverse("inventory:customer-list", request=request, format=format),
                "products": reverse("inventory:product-list", request=request, format=format),
                "invoices": reverse("inventory:invoice-list", request=request, format=format),
                "invoice_report": reverse("inventory:invoice-report", request=request, format=format),
            },
            "admin": "/admin/",
        }
    )
