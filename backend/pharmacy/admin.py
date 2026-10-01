from django.contrib import admin

from .models import Medicine, Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("medicine_id", "name", "category", "stock", "reorder_level", "expiry_date", "status")
    list_filter = ("category", "status")
    search_fields = ("medicine_id", "name", "generic_name", "manufacturer")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("prescription_id", "patient", "doctor", "date", "status")
    list_filter = ("status", "date")
    search_fields = ("prescription_id", "patient__name", "patient__patient_id")
    inlines = [PrescriptionItemInline]
