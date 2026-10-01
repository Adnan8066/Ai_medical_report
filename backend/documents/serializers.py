from django.conf import settings
from django.utils.text import get_valid_filename
from rest_framework import serializers

from .models import AISummary, DocumentChunk, ExtractedText, MedicalDocument
from .services.ai import AI_DISCLAIMER


def validate_upload(file):
    """
    Validate an uploaded medical document.

    Checks the extension, the declared content type, the size and normalises
    the file name so nothing dangerous or unexpected reaches the filesystem.
    """
    name = file.name or "document"
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise serializers.ValidationError(
            "Unsupported file type. Allowed types: "
            + ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS).upper()
            + "."
        )
    if file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise serializers.ValidationError(
            f"The file is too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB."
        )
    content_type = (getattr(file, "content_type", "") or "").lower()
    if content_type and content_type not in settings.ALLOWED_UPLOAD_CONTENT_TYPES:
        raise serializers.ValidationError(
            "The uploaded file does not match an accepted document format."
        )
    cleaned = get_valid_filename(name)
    if not cleaned or cleaned in {".", ".."}:
        raise serializers.ValidationError("The file name is not valid.")
    file.name = cleaned
    return file


class ExtractedTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedText
        fields = [
            "text",
            "language",
            "engine",
            "confidence",
            "page_count",
            "char_count",
            "preprocessing_notes",
            "processed_at",
        ]


class AISummarySerializer(serializers.ModelSerializer):
    disclaimer = serializers.SerializerMethodField()

    class Meta:
        model = AISummary
        fields = [
            "summary",
            "key_points",
            "medications",
            "lab_values",
            "important_dates",
            "classification",
            "provider",
            "model_name",
            "confidence",
            "generated_at",
            "disclaimer",
        ]

    def get_disclaimer(self, obj):
        return AI_DISCLAIMER


class MedicalDocumentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    ocr_status_label = serializers.CharField(
        source="get_ocr_status_display", read_only=True
    )
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.full_name", read_only=True, default=None
    )
    file_url = serializers.SerializerMethodField()
    extracted_text = ExtractedTextSerializer(read_only=True)
    ai_summary = AISummarySerializer(read_only=True)
    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = MedicalDocument
        fields = [
            "id",
            "document_id",
            "patient",
            "patient_name",
            "patient_code",
            "category",
            "category_label",
            "title",
            "description",
            "file",
            "file_url",
            "original_filename",
            "file_size",
            "mime_type",
            "checksum",
            "document_date",
            "tags",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
            "ocr_status",
            "ocr_status_label",
            "ocr_error",
            "extracted_text",
            "ai_summary",
            "chunk_count",
            "updated_at",
        ]
        read_only_fields = [
            "document_id",
            "file_size",
            "mime_type",
            "checksum",
            "uploaded_at",
            "uploaded_by",
            "ocr_status",
            "ocr_error",
            "updated_at",
        ]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url

    def get_chunk_count(self, obj):
        return obj.chunks.count() if hasattr(obj, "chunks") else 0


class MedicalDocumentWriteSerializer(serializers.ModelSerializer):
    file = serializers.FileField(validators=[validate_upload])

    class Meta:
        model = MedicalDocument
        fields = [
            "id",
            "patient",
            "category",
            "title",
            "description",
            "file",
            "document_date",
            "tags",
        ]


class DocumentChunkSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)
    document_code = serializers.CharField(source="document.document_id", read_only=True)

    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "document",
            "document_title",
            "document_code",
            "chunk_index",
            "text",
            "source_label",
            "token_estimate",
            "created_at",
        ]
