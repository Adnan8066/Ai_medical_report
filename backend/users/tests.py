"""Authentication, role matrix and object-level scoping tests."""

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from .models import RoleCode, User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="demo.admin",
            email="demo.admin@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.HOSPITAL_ADMIN,
            is_demo=True,
        )

    def test_login_with_email_returns_tokens_and_profile(self):
        response = self.client.post(
            "/api/auth/login/",
            {"identifier": "demo.admin@asternova.demo", "password": "DemoPass!234"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data["tokens"])
        self.assertEqual(response.data["user"]["role"], RoleCode.HOSPITAL_ADMIN)
        self.assertIn("permissions", response.data["user"])

    def test_login_with_username_also_works(self):
        response = self.client.post(
            "/api/auth/login/",
            {"identifier": "demo.admin", "password": "DemoPass!234"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_login_with_wrong_password_is_rejected(self):
        response = self.client.post(
            "/api/auth/login/",
            {"identifier": "demo.admin@asternova.demo", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.data)

    def test_anonymous_access_is_rejected(self):
        self.assertEqual(self.client.get("/api/patients/").status_code, 401)

    def test_me_returns_permission_matrix(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["permissions"].get("patients"))

    def test_failed_login_is_audited(self):
        from audit.models import AuditLog

        self.client.post(
            "/api/auth/login/",
            {"identifier": "demo.admin@asternova.demo", "password": "nope"},
            format="json",
        )
        self.assertTrue(AuditLog.objects.filter(action="Failed login").exists())

    def test_demo_password_setting_is_documented(self):
        self.assertTrue(settings.DEMO_PASSWORD)


class PermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.receptionist = User.objects.create_user(
            username="demo.reception",
            email="demo.reception@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.RECEPTIONIST,
        )
        self.pharmacist = User.objects.create_user(
            username="demo.pharmacist",
            email="demo.pharmacist@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.PHARMACIST,
        )

    def test_receptionist_cannot_read_audit_logs(self):
        self.client.force_authenticate(self.receptionist)
        self.assertEqual(self.client.get("/api/audit/").status_code, 403)

    def test_receptionist_can_read_patient_list(self):
        self.client.force_authenticate(self.receptionist)
        self.assertEqual(self.client.get("/api/patients/").status_code, 200)

    def test_pharmacist_cannot_create_patient(self):
        self.client.force_authenticate(self.pharmacist)
        response = self.client.post(
            "/api/patients/",
            {"name": "Not Allowed", "phone": "+91 9000000000 (demo)"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_super_admin_bypasses_module_matrix(self):
        admin = User.objects.create_superuser(
            username="root", email="root@asternova.demo", password="DemoPass!234"
        )
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get("/api/audit/").status_code, 200)
