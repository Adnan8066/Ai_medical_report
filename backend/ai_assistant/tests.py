"""Hospital assistant and document assistant behaviour tests."""

from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from beds.models import Bed, Ward
from emergency.models import EmergencyVisit
from patients.models import Patient
from pharmacy.models import Medicine
from users.models import RoleCode, User

from .engine import answer_question


class AssistantEngineTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="ai.admin",
            email="ai.admin@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.HOSPITAL_ADMIN,
        )
        self.patient_user = User.objects.create_user(
            username="ai.patient",
            email="ai.patient@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.PATIENT,
        )
        self.ward = Ward.objects.create(name="Demo Ward", code="DW01", category="general")
        Bed.objects.create(bed_number="G-001", ward=self.ward, status=Bed.Status.AVAILABLE)
        Bed.objects.create(bed_number="G-002", ward=self.ward, status=Bed.Status.OCCUPIED)
        Medicine.objects.create(
            medicine_id="MED-90001", name="ORS Sachet", stock=0, reorder_level=50
        )
        self.ward_patient = Patient.objects.create(
            patient_id="PAT-40001", name="Emergency Demo", phone="+91 9000000031 (demo)"
        )
        EmergencyVisit.objects.create(
            case_id="ER-90001",
            patient=self.ward_patient,
            priority=EmergencyVisit.Priority.CRITICAL,
            status=EmergencyVisit.Status.IN_TREATMENT,
        )

    def test_bed_question_reports_live_occupancy(self):
        result = answer_question("Which beds are available?", self.admin)
        self.assertEqual(result["intent"], "beds")
        self.assertEqual(result["data"]["available"], 1)
        self.assertEqual(result["data"]["total"], 2)

    def test_low_stock_question_lists_flagged_medicines(self):
        result = answer_question("Which medicines are low in stock?", self.admin)
        self.assertEqual(result["intent"], "pharmacy")
        names = [row["name"] for row in result["data"]["results"]]
        self.assertIn("ORS Sachet", names)

    def test_emergency_question_lists_todays_cases(self):
        result = answer_question("Show today's emergency patients", self.admin)
        self.assertEqual(result["intent"], "emergency")
        self.assertEqual(result["data"]["critical"], 1)

    def test_role_without_permission_is_refused(self):
        result = answer_question("Show today's emergency patients", self.patient_user)
        self.assertEqual(result["intent"], "denied")
        self.assertIn("permission", result["answer"].lower())

    def test_unknown_question_offers_guidance(self):
        result = answer_question("What is the weather in Kochi?", self.admin)
        self.assertEqual(result["intent"], "unknown")
        self.assertTrue(result["suggestions"])

    def test_every_answer_carries_the_safety_disclaimer(self):
        result = answer_question("Which beds are available?", self.admin)
        self.assertIn("authorized healthcare professional", result["disclaimer"])

    def test_assistant_never_offers_clinical_advice_intents(self):
        result = answer_question("Diagnose my chest pain and prescribe medicine", self.admin)
        self.assertNotEqual(result["intent"], "diagnosis")
        self.assertTrue(
            result["intent"] in {"pharmacy", "unknown", "documents", "laboratory", "billing"}
        )


class AssistantApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="api.admin",
            email="api.admin@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.HOSPITAL_ADMIN,
        )
        self.client.force_authenticate(self.admin)

    def test_ask_endpoint_persists_the_conversation(self):
        from .models import ChatMessage, ChatSession

        response = self.client.post(
            "/api/ai/ask/", {"question": "Which beds are available?"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "beds")
        self.assertEqual(ChatSession.objects.count(), 1)
        self.assertEqual(ChatMessage.objects.count(), 2)

    def test_capabilities_endpoint_documents_limits(self):
        response = self.client.get("/api/ai/capabilities/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["cannot"])
        self.assertIn("disclaimer", response.data)

    def test_document_assistant_without_documents_does_not_invent_content(self):
        patient = Patient.objects.create(
            patient_id="PAT-40002", name="No Docs", phone="+91 9000000032 (demo)"
        )
        response = self.client.post(
            "/api/ai/documents/ask/",
            {"question": "What medications are mentioned?", "patient": patient.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("No matching content", response.data["answer"])
        self.assertEqual(response.data["results"], [])
