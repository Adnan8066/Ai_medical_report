"""Medical document storage, OCR output, AI summaries and RAG chunks."""

from django.conf import settings
from django.db import models


class MedicalDocument(models.Model):
    class Category(models.TextChoices):
        LAB_REPORT = "lab_report", "Lab Report"
        PRESCRIPTION = "prescription", "Prescription"
        DISCHARGE_SUMMARY = "discharge_summary", "Discharge Summary"
        MEDICAL_CERTIFICATE = "medical_certificate", "Medical Certificate"
        REFERRAL_LETTER = "referral_letter", "Referral Letter"
        IMAGING_REPORT = "imaging_report", "Imaging Report"
        INSURANCE_DOCUMENT = "insurance_document", "Insurance Document"
        CONSULTATION_NOTE = "consultation_note", "Consultation Note"
        CONSENT_FORM = "consent_form", "Consent Form"
        OTHER = "other", "Other"

    class OCRStatus(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    document_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="documents"
    )
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.OTHER
    )
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to="medical_documents/%Y/%m/")
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0, help_text="Size in bytes.")
    mime_type = models.CharField(max_length=80, blank=True)
    checksum = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 of the file contents, used for duplicate detection.",
    )
    document_date = models.DateField(null=True, blank=True)
    tags = models.CharField(max_length=250, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents_uploaded",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ocr_status = models.CharField(
        max_length=20, choices=OCRStatus.choices, default=OCRStatus.UPLOADED
    )
    ocr_error = models.CharField(max_length=250, blank=True)
    is_demo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["patient", "-uploaded_at"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.document_id} - {self.title}"


class ExtractedText(models.Model):
    """Raw OCR output for a document."""

    document = models.OneToOneField(
        MedicalDocument, on_delete=models.CASCADE, related_name="extracted_text"
    )
    text = models.TextField(blank=True)
    language = models.CharField(max_length=20, default="eng")
    engine = models.CharField(max_length=40, default="tesseract")
    confidence = models.FloatField(null=True, blank=True)
    page_count = models.PositiveSmallIntegerField(default=1)
    char_count = models.PositiveIntegerField(default=0)
    preprocessing_notes = models.CharField(max_length=250, blank=True)
    processed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Extracted text for {self.document.document_id}"


class AISummary(models.Model):
    """
    Administrative summary of a document.

    The platform is deliberately limited to organisation and retrieval: no
    diagnosis, prescribing or treatment recommendation is produced or stored.
    """

    document = models.OneToOneField(
        MedicalDocument, on_delete=models.CASCADE, related_name="ai_summary"
    )
    summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list, blank=True)
    medications = models.JSONField(default=list, blank=True)
    lab_values = models.JSONField(default=list, blank=True)
    important_dates = models.JSONField(default=list, blank=True)
    organisations = models.JSONField(default=list, blank=True)
    classification = models.CharField(max_length=60, blank=True)
    provider = models.CharField(max_length=30, default="demo")
    model_name = models.CharField(max_length=60, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)
    is_demo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "AI summary"
        verbose_name_plural = "AI summaries"

    def __str__(self):
        return f"AI summary for {self.document.document_id}"


class DocumentChunk(models.Model):
    """A retrievable slice of extracted text with its vector embedding."""

    document = models.ForeignKey(
        MedicalDocument, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_index = models.PositiveIntegerField(default=0)
    text = models.TextField()
    embedding = models.JSONField(default=list, blank=True)
    source_label = models.CharField(max_length=200, blank=True)
    token_estimate = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        unique_together = [("document", "chunk_index")]

    def __str__(self):
        return f"{self.document.document_id} #{self.chunk_index}"
