from django.contrib import admin

from .models import Surgery


@admin.register(Surgery)
class SurgeryAdmin(admin.ModelAdmin):
    list_display = (
        "surgery_id",
        "patient",
        "surgery_name",
        "surgeon",
        "ot_room",
        "date",
        "start_time",
        "status",
    )
    list_filter = ("status", "department", "ot_room", "date")
    search_fields = ("surgery_id", "patient__name", "surgery_name")
    filter_horizontal = ("nurses",)
    date_hierarchy = "date"
