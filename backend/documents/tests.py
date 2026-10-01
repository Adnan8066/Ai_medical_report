"""Upload validation, OCR pipeline, AI summarisation and RAG retrieval."""

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from hospital.demodata.builders_documents import build_pdf
from patients.models import Patient
from users.models import RoleCode, User

from .models import AISummary, DocumentChunk, ExtractedText, MedicalDocument
from .services import ai, rag

MEDIA_ROOT = tempfile.mkdtemp(prefix="asternova-test-media-")

PRESCRIPTION_TEXT = [
    "ASTERNOVA DEMO PRESCRIPTION",
    "1. Tab. Paracetamol 500 mg twice daily for 5 days",
    "2. Tab. Metformin 500 mg once daily for 30 days",
    "Hemoglobin 13.8 g/dL Reference range 13.5 - 17.5 g/dL",
    "Date of visit: 12/03/2024",
]


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DocumentPipelineTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.doctor = User.objects.create_user(
            username="doc.uploader",
            email="doc.uploader@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.HOSPITAL_ADMIN,
        )
        self.patient = Patient.objects.create(
            patient_id="PAT-30001",
            name="Upload Test Patient",
            phone="+91 9000000021 (demo)",
        )
        self.client.force_authenticate(self.doctor)

    def _upload(self, name="prescription.pdf", content_type="application/pdf", payload=None):
        file = SimpleUploadedFile(
            name, payload or build_pdf(PRESCRIPTION_TEXT), content_type=content_type
        )
        return self.client.post(
            "/api/documents/",
            {"patient": self.patient.id, "category": "prescription", "title": "Demo Rx", "file": file},
            format="multipart",
        )

    def test_upload_runs_ocr_ai_and_indexing(self):
        response = self._upload()
        self.assertEqual(response.status_code, 201, response.data)
        document = MedicalDocument.objects.get()
        self.assertTrue(document.document_id.startswith("DOC-"))
        self.assertTrue(document.checksum)
        self.assertEqual(document.ocr_status, MedicalDocument.OCRStatus.COMPLETED)

        extracted = ExtractedText.objects.get(document=document)
        self.assertIn("Paracetamol", extracted.text)

        summary = AISummary.objects.get(document=document)
        medications = [item["name"] for item in summary.medications]
        self.assertIn("Paracetamol", medications)
        self.assertTrue(any(value["name"] == "Hemoglobin" for value in summary.lab_values))
        self.assertIn("administrative", ai.AI_DISCLAIMER.lower())

        self.assertGreater(DocumentChunk.objects.filter(document=document).count(), 0)

    def test_summary_endpoint_returns_text_and_disclaimer(self):
        document_id = self._upload().data["id"]
        response = self.client.get(f"/api/documents/{document_id}/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Paracetamol", response.data["extracted_text"])
        self.assertEqual(response.data["disclaimer"], ai.AI_DISCLAIMER)

    def test_rag_search_finds_the_uploaded_document(self):
        self._upload()
        response = self.client.get("/api/documents/search/", {"q": "paracetamol"})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data["results"]), 0)
        self.assertIn("documents", response.data["answer"].lower())

    def test_rag_search_requires_a_query(self):
        self.assertEqual(self.client.get("/api/documents/search/").status_code, 400)

    def test_unsupported_file_type_is_rejected(self):
        response = self._upload(
            name="malware.exe", content_type="application/octet-stream", payload=b"MZ binary"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data["errors"])
        self.assertEqual(MedicalDocument.objects.count(), 0)

    def test_oversized_file_is_rejected(self):
        from django.conf import settings

        payload = b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
        response = self._upload(name="big.pdf", payload=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data["errors"])

    def test_ocr_status_endpoint_reports_engine_availability(self):
        response = self.client.get("/api/documents/ocr_status/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("engine", response.data["ocr"])
        self.assertIn("provider", response.data["ai"])

    def test_documents_are_scoped_to_the_patient(self):
        self._upload()
        other_user = User.objects.create_user(
            username="portal.patient2",
            email="portal.patient2@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.PATIENT,
        )
        self.patient.user = other_user
        self.patient.save(update_fields=["user"])

        stranger = Patient.objects.create(
            patient_id="PAT-30002", name="Other Patient", phone="+91 9000000022 (demo)"
        )
        MedicalDocument.objects.create(
            document_id="DOC-99999",
            patient=stranger,
            category="other",
            title="Not mine",
            file="medical_documents/demo.pdf",
        )

        self.client.force_authenticate(other_user)
        response = self.client.get("/api/documents/")
        titles = [row["title"] for row in response.data["results"]]
        self.assertEqual(titles, ["Demo Rx"])


class RagUnitTests(TestCase):
    def test_chunking_overlaps_and_covers_the_text(self):
        text = " ".join(f"word{i}" for i in range(300))
        chunks = rag.chunk_text(text, size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].split()[0], "word0")

    def test_embeddings_are_normalised_and_similar_text_scores_higher(self):
        left = rag.embed("paracetamol tablet twice daily")
        right = rag.embed("paracetamol tablet twice daily")
        unrelated = rag.embed("coronary angiography report")
        self.assertAlmostEqual(rag.cosine_similarity(left, right), 1.0, places=5)
        self.assertGreater(
            rag.cosine_similarity(left, right), rag.cosine_similarity(left, unrelated)
        )
