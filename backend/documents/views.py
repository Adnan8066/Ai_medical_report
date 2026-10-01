import hashlib

from django.db.models import Count, Q
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.viewsets import BaseViewSet
from patients.models import Patient

from .models import MedicalDocument
from .pipeline import process_document
from .serializers import (
    AISummarySerializer,
    DocumentChunkSerializer,
    MedicalDocumentSerializer,
    MedicalDocumentWriteSerializer,
)
from .services import ai, ocr, rag


def _checksum(file_field):
    digest = hashlib.sha256()
    file_field.seek(0)
    for chunk in file_field.chunks():
        digest.update(chunk)
    file_field.seek(0)
    return digest.hexdigest()


class MedicalDocumentViewSet(BaseViewSet):
    module = "documents"
    queryset = MedicalDocument.objects.select_related("patient", "uploaded_by").all()
    search_fields = ["document_id", "title", "description", "tags", "patient__name"]
    ordering_fields = ["uploaded_at", "title", "document_date"]
    ordering = ["-uploaded_at"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return MedicalDocumentWriteSerializer
        return MedicalDocumentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if category := params.get("category"):
            queryset = queryset.filter(category=category)
        if ocr := params.get("ocr_status"):
            queryset = queryset.filter(ocr_status=ocr)
        if params.get("has_summary") == "true":
            queryset = queryset.filter(ai_summary__isnull=False)
        if search := params.get("search"):
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(tags__icontains=search)
                | Q(document_id__icontains=search)
            )
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Upload a document, then immediately run OCR -> RAG -> AI summarisation.

        Passing ``?process=false`` stores the file only, which is useful when
        the pipeline is moved to a background worker.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]

        checksum = _checksum(upload)
        from config.ids import next_sequential_id

        document = MedicalDocument(
            document_id=next_sequential_id(MedicalDocument, "document_id", "DOC", width=5),
            patient=serializer.validated_data["patient"],
            category=serializer.validated_data.get("category", MedicalDocument.Category.OTHER),
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            document_date=serializer.validated_data.get("document_date"),
            tags=serializer.validated_data.get("tags", ""),
            original_filename=upload.name,
            file_size=upload.size,
            mime_type=getattr(upload, "content_type", "") or "",
            checksum=checksum,
            uploaded_by=request.user,
        )
        document.file.save(upload.name, upload, save=False)
        document.save()
        self._audit("Uploaded", document)

        result = None
        if str(request.query_params.get("process", "true")).lower() != "false":
            result = process_document(document)

        payload = MedicalDocumentSerializer(document, context={"request": request}).data
        if result is not None:
            payload["pipeline"] = {
                "engine": result["engine"],
                "char_count": result["char_count"],
                "chunks_indexed": result["chunks_indexed"],
                "ocr_status": result["ocr_status"],
                "message": result["message"],
                "ai_provider": (result["summary"] or {}).get("provider"),
            }
        return Response(payload, status=http_status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Re-run the OCR / AI pipeline (for example after installing Tesseract)."""
        document = self.get_object()
        result = process_document(document, run_ai=request.data.get("run_ai", True))
        self._audit("Reprocessed", document)
        return Response(
            {
                "document": MedicalDocumentSerializer(
                    document, context={"request": request}
                ).data,
                "engine": result["engine"],
                "char_count": result["char_count"],
                "chunks_indexed": result["chunks_indexed"],
                "message": result["message"],
            }
        )

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """AI summary, extracted text and the safety disclaimer."""
        document = self.get_object()
        summary = getattr(document, "ai_summary", None)
        extracted = getattr(document, "extracted_text", None)
        return Response(
            {
                "document": document.document_id,
                "title": document.title,
                "ocr_status": document.ocr_status,
                "ocr_error": document.ocr_error,
                "extracted_text": extracted.text if extracted else "",
                "engine": extracted.engine if extracted else None,
                "confidence": extracted.confidence if extracted else None,
                "summary": AISummarySerializer(summary).data if summary else None,
                "disclaimer": ai.AI_DISCLAIMER,
            }
        )

    @action(detail=True, methods=["get"])
    def chunks(self, request, pk=None):
        document = self.get_object()
        return Response(
            DocumentChunkSerializer(document.chunks.all(), many=True).data
        )

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Retrieval-Augmented search across the documents the caller may see.

        Only authorised documents are searched - a patient query never reaches
        another patient's files.
        """
        query = (request.query_params.get("q") or "").strip()
        if not query:
            return Response(
                {
                    "detail": "Enter a question or keyword to search the documents.",
                    "code": "invalid",
                    "errors": {"q": "This parameter is required."},
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        documents = self.get_queryset()
        patient_id = request.query_params.get("patient")
        patient_name = ""
        if patient_id:
            documents = documents.filter(patient_id=patient_id)
            patient = Patient.objects.filter(pk=patient_id).first()
            patient_name = patient.name if patient else ""

        results = rag.search(query, documents)
        answer, sources = rag.build_answer(query, results, patient_name=patient_name)
        return Response(
            {
                "query": query,
                "answer": answer,
                "mode": "demo" if not (ai.settings.AI_PROVIDER == "openai") else "openai",
                "results": results,
                "sources": sources,
                "disclaimer": ai.AI_DISCLAIMER,
                "grounding": (
                    "Answers are composed only from the retrieved document text. "
                    "Nothing is invented."
                ),
            }
        )

    @action(detail=False, methods=["get"])
    def duplicates(self, request):
        """Flag documents whose checksum matches another upload."""
        duplicates = (
            MedicalDocument.objects.values("checksum", "patient__name")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .exclude(checksum="")
        )
        payload = []
        for row in duplicates:
            docs = MedicalDocument.objects.filter(checksum=row["checksum"])
            payload.append(
                {
                    "checksum": row["checksum"],
                    "count": row["total"],
                    "patient": row["patient__name"],
                    "documents": MedicalDocumentSerializer(
                        docs, many=True, context={"request": request}
                    ).data,
                }
            )
        return Response({"count": len(payload), "groups": payload})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def ocr_status(self, request):
        """Report whether the Tesseract engine is available on this host."""
        return Response({"ocr": ocr.ocr_status(), "ai": ai.answer_status()})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "uploaded": queryset.filter(
                    ocr_status=MedicalDocument.OCRStatus.UPLOADED
                ).count(),
                "processing": queryset.filter(
                    ocr_status=MedicalDocument.OCRStatus.PROCESSING
                ).count(),
                "completed": queryset.filter(
                    ocr_status=MedicalDocument.OCRStatus.COMPLETED
                ).count(),
                "failed": queryset.filter(
                    ocr_status=MedicalDocument.OCRStatus.FAILED
                ).count(),
                "summarised": queryset.filter(ai_summary__isnull=False).count(),
                "chunks": sum(item.chunks.count() for item in queryset[:500]),
                "by_category": list(
                    queryset.values("category").annotate(total=Count("id")).order_by("-total")
                ),
            }
        )
