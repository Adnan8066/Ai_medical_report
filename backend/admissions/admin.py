from django.contrib import admin

from .models import Admission, DischargeSummary


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = (
        "admission_id",
        "patient",
        "doctor",
        "department",
        "bed_number",
        "admission_date",
        "status",
    )
    list_filter = ("status", "department", "ward")
    search_fields = ("admission_id", "patient__name", "patient__patient_id")
    date_hierarchy = "admission_date"


@admin.register(DischargeSummary)
class DischargeSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "discharge_id",
        "patient",
        "doctor",
        "discharge_date",
        "status",
        "doctor_approved",
    )
    list_filter = ("status", "doctor_approved")
    search_fields = ("discharge_id", "patient__name", "patient__patient_id")
