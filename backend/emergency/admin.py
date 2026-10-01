from django.contrib import admin

from .models import EmergencyVisit


@admin.register(EmergencyVisit)
class EmergencyVisitAdmin(admin.ModelAdmin):
    list_display = (
        "case_id",
        "patient",
        "arrival_time",
        "priority",
        "assigned_doctor",
        "status",
    )
    list_filter = ("priority", "status", "arrival_time")
    search_fields = ("case_id", "patient__name", "patient__patient_id")
    date_hierarchy = "arrival_time"
