from django.contrib import admin

from .models import RadiologyReport


@admin.register(RadiologyReport)
class RadiologyReportAdmin(admin.ModelAdmin):
    list_display = ("scan_id", "patient", "scan_type", "body_part", "status", "report_date")
    list_filter = ("scan_type", "status")
    search_fields = ("scan_id", "patient__name", "patient__patient_id")
    date_hierarchy = "appointment_date"
