from django.contrib import admin

from .models import Bed, Ward


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "department", "floor")
    list_filter = ("category", "department")
    search_fields = ("name", "code")


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ("bed_number", "ward", "category", "status", "patient")
    list_filter = ("status", "category", "ward")
    search_fields = ("bed_number", "room_number", "patient__name")
