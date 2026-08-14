from django.db import transaction
from rest_framework import serializers

from .models import Category, Customer, Invoice, InvoiceItem, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Category name cannot be blank.")
        return value.strip()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_name",
            "description",
            "price",
            "quantity_in_stock",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_quantity_in_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value

    def validate_sku(self, value):
        if not value.strip():
            raise serializers.ValidationError("SKU cannot be blank.")
        return value.strip().upper()


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone_number", "address", "created_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Customer name cannot be blank.")
        return value.strip()


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal"]

    def get_subtotal(self, obj):
        return obj.subtotal

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Nested-write serializer: accepts a list of {product, quantity, unit_price}
    items alongside the invoice itself, validates stock availability,
    and decrements product stock atomically on creation.
    """

    items = InvoiceItemSerializer(many=True)
    created_by = serializers.ReadOnlyField(source="created_by.username")
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    total_amount = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "customer",
            "customer_name",
            "status",
            "created_by",
            "items",
            "total_amount",
            "total_quantity",
            "created_at",
            "updated_at",
        ]

    def get_total_amount(self, obj):
        return obj.total_amount

    def get_total_quantity(self, obj):
        return obj.total_quantity

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("An invoice must contain at least one item.")
        return value

    def validate(self, attrs):
        items = attrs.get("items", [])
        for item in items:
            product = item["product"]
            quantity = item["quantity"]
            # On update, existing items are replaced, so we validate against
            # current stock; this is a simple check suitable for this scope.
            if quantity > product.quantity_in_stock:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Insufficient stock for '{product.name}'. "
                            f"Available: {product.quantity_in_stock}, requested: {quantity}."
                        )
                    }
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context["request"]
        invoice = Invoice.objects.create(created_by=request.user, **validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
            product = item_data["product"]
            product.quantity_in_stock -= item_data["quantity"]
            product.save(update_fields=["quantity_in_stock"])

        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        instance.status = validated_data.get("status", instance.status)
        instance.customer = validated_data.get("customer", instance.customer)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance
