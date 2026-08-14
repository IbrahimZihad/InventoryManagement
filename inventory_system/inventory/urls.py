from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CustomerViewSet,
    InvoiceReportView,
    InvoiceViewSet,
    ProductViewSet,
)

app_name = "inventory"

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    # NOTE: must come before include(router.urls) so it takes precedence
    # over the router's /invoices/{pk}/ detail pattern.
    path("invoices/report/", InvoiceReportView.as_view(), name="invoice-report"),
    path("", include(router.urls)),
]
