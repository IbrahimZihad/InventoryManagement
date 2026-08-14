from django.db import transaction
from rest_framework import serializers

from .models import Category, Customer, Invoice, InvoiceItem, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "description", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name cannot be blank.")
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone_number", "address", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Customer name cannot be blank.")
        return value

    def validate_phone_number(self, value):
        if value and not value.replace("+", "").replace(" ", "").isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits, spaces, or a leading +."
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = (
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
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_quantity_in_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value

    def validate_sku(self, value):
        value = value.strip().upper()
        qs = Product.objects.filter(sku__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ("id", "product", "product_name", "quantity", "unit_price", "subtotal")
        read_only_fields = ("id", "subtotal")

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value

    def validate(self, attrs):
        product = attrs.get("product") or getattr(self.instance, "product", None)
        quantity = attrs.get("quantity") or getattr(self.instance, "quantity", None)
        if product and quantity and product.quantity_in_stock < quantity:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.quantity_in_stock} units of '{product.name}' are in stock."}
            )
        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    total_amount = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "customer",
            "customer_name",
            "status",
            "items",
            "total_amount",
            "total_quantity",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "invoice_number", "created_by", "created_at", "updated_at")

    def get_total_amount(self, obj):
        return obj.total_amount

    def get_total_quantity(self, obj):
        return obj.total_quantity

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("An invoice must contain at least one item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context["request"]
        invoice = Invoice.objects.create(created_by=request.user, **validated_data)

        for item_data in items_data:
            product = item_data["product"]
            quantity = item_data["quantity"]
            InvoiceItem.objects.create(invoice=invoice, **item_data)
            product.quantity_in_stock -= quantity
            product.save(update_fields=["quantity_in_stock"])

        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Restock products tied to the old line items before replacing them.
            for old_item in instance.items.all():
                product = old_item.product
                product.quantity_in_stock += old_item.quantity
                product.save(update_fields=["quantity_in_stock"])
            instance.items.all().delete()

            for item_data in items_data:
                product = item_data["product"]
                quantity = item_data["quantity"]
                InvoiceItem.objects.create(invoice=instance, **item_data)
                product.quantity_in_stock -= quantity
                product.save(update_fields=["quantity_in_stock"])

        return instance


class InvoiceReportSerializer(serializers.Serializer):
    total_invoices = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_products_sold = serializers.IntegerField()
    average_invoice_value = serializers.DecimalField(max_digits=16, decimal_places=2)
