from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "patient",
        "date",
        "patient_payable",
        "paid_amount",
        "payment_status",
    )
    list_filter = ("payment_status", "payment_method", "date")
    search_fields = ("invoice_number", "patient__name", "patient__patient_id")
    inlines = [InvoiceItemInline]
    date_hierarchy = "date"
