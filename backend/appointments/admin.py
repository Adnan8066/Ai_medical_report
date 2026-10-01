from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "appointment_id",
        "patient",
        "doctor",
        "department",
        "date",
        "time",
        "status",
    )
    list_filter = ("status", "appointment_type", "department", "date")
    search_fields = ("appointment_id", "patient__name", "patient__patient_id")
    date_hierarchy = "date"
    autocomplete_fields = ("patient", "doctor")
