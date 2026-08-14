from django.contrib import admin

from .models import Category, Customer, Invoice, InvoiceItem, Product


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("invoice_number", "customer__name")
    readonly_fields = ("invoice_number",)
    inlines = [InvoiceItemInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "quantity_in_stock")
    list_filter = ("category",)
    search_fields = ("name", "sku")


admin.site.register(Category)
admin.site.register(Customer)
