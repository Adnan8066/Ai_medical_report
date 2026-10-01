from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "department",
        "is_active",
        "is_demo",
    )
    list_filter = ("role", "is_active", "is_demo", "department")
    search_fields = ("username", "email", "first_name", "last_name", "employee_id")
    ordering = ("first_name", "last_name")

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "AsterNova platform",
            {
                "fields": (
                    "role",
                    "employee_id",
                    "phone",
                    "department",
                    "designation",
                    "avatar",
                    "is_demo",
                    "last_seen",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "AsterNova platform",
            {"fields": ("email", "role", "employee_id", "department")},
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_system")
    search_fields = ("name", "code")
