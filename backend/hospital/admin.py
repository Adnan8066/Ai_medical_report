from django.contrib import admin

from .models import Department, Floor, Hospital, MapLocation


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "total_beds", "emergency_number")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "hod", "floor", "bed_count", "is_active")
    list_filter = ("is_clinical", "is_active")
    search_fields = ("name", "code")


class MapLocationInline(admin.TabularInline):
    model = MapLocation
    extra = 0


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "is_public")
    inlines = [MapLocationInline]


@admin.register(MapLocation)
class MapLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "floor", "category", "code", "is_landmark")
    list_filter = ("category", "floor")
    search_fields = ("name", "code", "keywords")
