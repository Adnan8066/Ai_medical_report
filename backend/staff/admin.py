from django.contrib import admin

from .models import Shift, ShiftAssignment, Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "name", "role", "department", "shift", "status")
    list_filter = ("role", "status", "department", "shift")
    search_fields = ("employee_id", "name", "contact", "email")


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "start_time", "end_time", "is_emergency_shift")


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ("staff", "shift", "date", "department", "status")
    list_filter = ("shift", "status", "date")
    search_fields = ("staff__name", "staff__employee_id")
    date_hierarchy = "date"
