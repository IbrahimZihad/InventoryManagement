from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("phone_number", "address", "bio", "avatar")}),
    )
    list_display = ["username", "email", "is_staff", "is_active", "date_joined"]
    search_fields = ["username", "email"]
