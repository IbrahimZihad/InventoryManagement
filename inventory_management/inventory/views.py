from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Customer, Invoice, InvoiceItem, Product
from .permissions import IsOwnerOrStaff, IsStaffOrReadOnly
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    InvoiceSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["name"]
    search_fields = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["category", "sku"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffOrReadOnly]


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    Staff/admin users see and can manage every invoice.
    Regular users only see invoices they created, and can only
    modify/delete their own (enforced by IsOwnerOrStaff).
    """

    serializer_class = InvoiceSerializer
    permission_classes = [IsOwnerOrStaff]
    filterset_fields = ["status", "customer"]

    def get_queryset(self):
        qs = Invoice.objects.select_related("customer", "created_by").prefetch_related("items__product")
        if self.request.user.is_staff:
            return qs
        return qs.filter(created_by=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class InvoiceReportView(APIView):
    """
    GET /api/inventory/report/
    Returns total invoices, total sales revenue, and total products sold.
    Staff users see figures across all invoices; regular users see
    figures scoped to invoices they created.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.all() if request.user.is_staff else Invoice.objects.filter(created_by=request.user)

        total_invoices = invoices.count()
        items = InvoiceItem.objects.filter(invoice__in=invoices)

        total_products_sold = items.aggregate(total=Sum("quantity"))["total"] or 0
        total_sales = sum((item.subtotal for item in items), start=0)

        invoices_by_status = {
            choice: invoices.filter(status=choice).count() for choice, _ in Invoice.Status.choices
        }

        return Response(
            {
                "total_invoices": total_invoices,
                "total_sales": str(total_sales),
                "total_products_sold": total_products_sold,
                "invoices_by_status": invoices_by_status,
            }
        )
