from django.contrib import admin

from .models import Category, Customer, Invoice, InvoiceItem, Product


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "category", "price", "quantity_in_stock", "created_by"]
    list_filter = ["category"]
    search_fields = ["name", "sku"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone_number"]
    search_fields = ["name", "email"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "status", "created_by", "total_amount", "created_at"]
    list_filter = ["status"]
    inlines = [InvoiceItemInline]
