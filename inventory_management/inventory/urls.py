from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, CustomerViewSet, InvoiceReportView, InvoiceViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("customers", CustomerViewSet, basename="customer")
router.register("invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("report/", InvoiceReportView.as_view(), name="invoice-report"),
    path("", include(router.urls)),
]
