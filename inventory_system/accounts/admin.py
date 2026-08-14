from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile


class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "is_staff", "is_active", "is_verified")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra", {"fields": ("phone_number", "is_verified")}),
    )


admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
