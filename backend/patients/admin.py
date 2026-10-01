from django.contrib import admin

from .models import NurseAssignment, Patient, Vitals


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "patient_id",
        "name",
        "gender",
        "blood_group",
        "department",
        "assigned_doctor",
        "patient_type",
        "current_status",
    )
    list_filter = ("patient_type", "current_status", "department", "gender", "blood_group")
    search_fields = ("patient_id", "name", "phone", "email")
    date_hierarchy = "registration_date"


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ("patient", "recorded_at", "temperature_c", "pulse_bpm", "spo2", "status")
    list_filter = ("status",)
    search_fields = ("patient__name", "patient__patient_id")


@admin.register(NurseAssignment)
class NurseAssignmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "nurse", "shift", "assigned_on", "status")
    list_filter = ("status", "assigned_on")
