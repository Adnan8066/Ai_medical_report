from django.contrib import admin

from .models import OPDVisit


@admin.register(OPDVisit)
class OPDVisitAdmin(admin.ModelAdmin):
    list_display = ("visit_id", "patient", "doctor", "visit_date", "diagnosis", "status")
    list_filter = ("status", "department", "visit_date")
    search_fields = ("visit_id", "patient__name", "patient__patient_id", "diagnosis")
    date_hierarchy = "visit_date"
