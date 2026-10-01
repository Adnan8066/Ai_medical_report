from django.contrib import admin

from .models import LabReport, LabTest


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "sample_type", "price")
    list_filter = ("category",)
    search_fields = ("code", "name")


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ("lab_id", "patient", "test", "status", "flag", "report_date")
    list_filter = ("status", "flag", "test__category")
    search_fields = ("lab_id", "patient__name", "patient__patient_id")
    date_hierarchy = "ordered_at"
