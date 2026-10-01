from django.contrib import admin

from .models import AISummary, DocumentChunk, ExtractedText, MedicalDocument


class ExtractedTextInline(admin.StackedInline):
    model = ExtractedText
    extra = 0


class AISummaryInline(admin.StackedInline):
    model = AISummary
    extra = 0


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "document_id",
        "title",
        "patient",
        "category",
        "ocr_status",
        "uploaded_at",
    )
    list_filter = ("category", "ocr_status")
    search_fields = ("document_id", "title", "patient__name", "patient__patient_id")
    date_hierarchy = "uploaded_at"
    inlines = [ExtractedTextInline, AISummaryInline]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "token_estimate", "created_at")
    search_fields = ("document__document_id", "document__title")
