from django.contrib import admin

from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "doctor_id",
        "name",
        "department",
        "designation",
        "is_hod",
        "availability",
        "status",
    )
    list_filter = ("department", "designation", "is_hod", "availability", "status")
    search_fields = ("doctor_id", "name", "specialization", "qualification")
    autocomplete_fields = ("department",)
    readonly_fields = ("created_at", "updated_at")
