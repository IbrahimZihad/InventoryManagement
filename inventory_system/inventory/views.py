from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Customer, Invoice, InvoiceItem, Product
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    InvoiceReportSerializer,
    InvoiceSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """Full CRUD for categories. Read = any authenticated user, write = staff only."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]


class CustomerViewSet(viewsets.ModelViewSet):
    """Full CRUD for customers. Any authenticated user may manage customers."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "email", "phone_number"]
    ordering_fields = ["name", "created_at"]


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for products. Read = any authenticated user, write = staff only."""

    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category"]
    search_fields = ["name", "sku", "category__name"]
    ordering_fields = ["price", "quantity_in_stock", "created_at"]


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for invoices. Any authenticated user can create invoices;
    only the creator (or staff) may update/delete them. Non-staff users
    only ever see their own invoices.
    """

    queryset = (
        Invoice.objects.select_related("customer", "created_by")
        .prefetch_related("items__product")
        .all()
    )
    serializer_class = InvoiceSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "customer"]
    search_fields = ["invoice_number", "customer__name"]
    ordering_fields = ["created_at", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(created_by=self.request.user)
        return qs


class InvoiceReportView(APIView):
    """
    GET /api/inventory/invoices/report/
    Aggregate stats: total invoices, total sales, total products sold,
    and average invoice value. Staff see stats across all invoices;
    regular users see stats scoped to their own invoices.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.all()
        if not request.user.is_staff:
            invoices = invoices.filter(created_by=request.user)

        total_invoices = invoices.count()

        item_qs = InvoiceItem.objects.filter(invoice__in=invoices).annotate(
            line_total=ExpressionWrapper(
                F("unit_price") * F("quantity"),
                output_field=DecimalField(max_digits=16, decimal_places=2),
            )
        )
        aggregates = item_qs.aggregate(
            total_sales=Sum("line_total"),
            total_products_sold=Sum("quantity"),
        )

        total_sales = aggregates["total_sales"] or Decimal("0.00")
        total_products_sold = aggregates["total_products_sold"] or 0
        average_invoice_value = (total_sales / total_invoices) if total_invoices else Decimal("0.00")

        data = {
            "total_invoices": total_invoices,
            "total_sales": total_sales,
            "total_products_sold": total_products_sold,
            "average_invoice_value": round(average_invoice_value, 2),
        }
        serializer = InvoiceReportSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
