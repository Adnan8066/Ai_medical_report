from django.contrib import admin

from .models import InsuranceClaim, InsurancePolicy, InsuranceProvider


@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "contact_person", "phone")
    search_fields = ("name", "code")


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ("policy_number", "patient", "provider", "coverage_amount", "valid_to", "status")
    list_filter = ("provider", "policy_type", "status")
    search_fields = ("policy_number", "patient__name", "patient__patient_id")


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = (
        "claim_number",
        "patient",
        "policy",
        "claim_amount",
        "approved_amount",
        "status",
        "submitted_date",
    )
    list_filter = ("status", "submitted_date")
    search_fields = ("claim_number", "patient__name", "patient__patient_id")
    date_hierarchy = "submitted_date"
