from django.contrib import admin

from .models import BloodIssue, BloodStock, Donation


@admin.register(BloodStock)
class BloodStockAdmin(admin.ModelAdmin):
    list_display = ("blood_group", "units_available", "units_reserved", "critical_threshold")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("donation_id", "donor_name", "blood_group", "units", "donation_date", "screening")
    list_filter = ("blood_group", "screening", "donation_date")
    search_fields = ("donation_id", "donor_name", "donor_code")


@admin.register(BloodIssue)
class BloodIssueAdmin(admin.ModelAdmin):
    list_display = ("issue_id", "blood_group", "units", "patient", "ward", "status")
    list_filter = ("blood_group", "status")
    search_fields = ("issue_id", "patient__name", "crossmatch_id")
