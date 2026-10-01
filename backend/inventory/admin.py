from django.contrib import admin

from .models import InventoryItem, PurchaseOrder, PurchaseOrderItem, StockMovement, Supplier


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "contact_person", "phone", "is_active")
    search_fields = ("code", "name", "contact_person")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("item_code", "name", "category", "stock", "reorder_level", "status")
    list_filter = ("category", "status")
    search_fields = ("item_code", "name", "batch_number")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "order_date", "expected_date", "status", "total_amount")
    list_filter = ("status", "supplier")
    search_fields = ("po_number",)
    inlines = [PurchaseOrderItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "movement_type", "quantity", "balance_after", "created_at")
    list_filter = ("movement_type",)
    search_fields = ("item__name", "item__item_code", "reference")
