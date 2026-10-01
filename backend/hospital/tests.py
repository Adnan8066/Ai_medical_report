"""Hospital profile, settings permissions and navigation tests."""

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import RoleCode, User

from .models import Department, Floor, Hospital, MapLocation
from .views import get_hospital


class HospitalSettingsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="settings.admin",
            email="settings.admin@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.HOSPITAL_ADMIN,
        )
        self.nurse = User.objects.create_user(
            username="settings.nurse",
            email="settings.nurse@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.NURSE,
        )

    def test_hospital_profile_is_created_on_demand(self):
        self.assertEqual(Hospital.objects.count(), 0)
        hospital = get_hospital()
        self.assertIn("AsterNova", hospital.name)
        self.assertEqual(Hospital.objects.count(), 1)

    def test_administrator_can_update_settings(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            "/api/hospital/", {"phone": "+91 484 400 9999 (demo)"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["phone"], "+91 484 400 9999 (demo)")

    def test_settings_change_is_audited(self):
        from audit.models import AuditLog

        self.client.force_authenticate(self.admin)
        self.client.patch("/api/hospital/", {"city": "Kochi"}, format="json")
        self.assertTrue(
            AuditLog.objects.filter(action="Updated hospital settings").exists()
        )

    def test_non_administrator_cannot_change_settings(self):
        self.client.force_authenticate(self.nurse)
        response = self.client.patch("/api/hospital/", {"phone": "x"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(get_hospital().phone, "x")

    def test_status_endpoint_reports_runtime_configuration(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/hospital/status/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("engine", response.data["ocr"])
        self.assertIn("provider", response.data["ai"])
        self.assertIn("max_size_mb", response.data["uploads"])


class NavigationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="nav.user",
            email="nav.user@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.RECEPTIONIST,
        )
        self.client.force_authenticate(self.user)
        floor = Floor.objects.create(number=0, name="Ground Floor")
        department = Department.objects.create(name="Cardiology", code="CARD")
        self.reception = MapLocation.objects.create(
            floor=floor, name="Main Reception", code="RCP-01", category="service",
            x=500, y=620, is_landmark=True,
        )
        self.cardiology = MapLocation.objects.create(
            floor=floor, name="Cardiology Clinic", code="CD-201", category="department",
            department=department, x=250, y=380, description="Heart clinic",
        )

    def test_search_finds_a_destination(self):
        response = self.client.get("/api/navigation/directions/", {"q": "cardio"})
        self.assertEqual(response.status_code, 200)
        names = [row["name"] for row in response.data["destinations"]]
        self.assertIn("Cardiology Clinic", names)

    def test_route_between_two_locations_returns_steps(self):
        response = self.client.get(
            "/api/navigation/directions/", {"to": self.cardiology.id}
        )
        self.assertEqual(response.status_code, 200)
        route = response.data["route"]
        self.assertTrue(route["same_floor"])
        self.assertGreaterEqual(len(route["steps"]), 3)
        self.assertGreater(route["estimated_minutes"], 0)
        self.assertIn("lift", route["accessibility_note"].lower())

    def test_route_requires_a_destination(self):
        response = self.client.get("/api/navigation/directions/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["route"])
