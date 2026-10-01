"""Patient registration, validation, scoping and timeline tests."""

from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from hospital.models import Department
from users.models import RoleCode, User

from .models import Patient


class PatientApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="p.admin",
            email="p.admin@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.HOSPITAL_ADMIN,
        )
        self.department = Department.objects.create(name="Cardiology", code="CARD")
        self.client.force_authenticate(self.admin)

    def test_registration_creates_patient_and_assigns_an_identifier(self):
        response = self.client.post(
            "/api/patients/",
            {
                "name": "Rahul Krishnan",
                "date_of_birth": "1980-05-14",
                "gender": "male",
                "blood_group": "B+",
                "phone": "+91 9847012345 (demo)",
                "department": self.department.id,
                "patient_type": "opd",
                "current_status": "registered",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        patient = Patient.objects.get()
        self.assertTrue(patient.patient_id.startswith("PAT-"))
        self.assertEqual(patient.age, date.today().year - 1980 - (
            (date.today().month, date.today().day) < (5, 14)
        ))

    def test_short_phone_number_is_rejected_with_a_friendly_message(self):
        response = self.client.post(
            "/api/patients/",
            {"name": "Short Phone", "phone": "12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.data["errors"])

    def test_doctor_must_belong_to_the_selected_department(self):
        from doctors.models import Doctor

        other = Department.objects.create(name="Neurology", code="NEUR")
        doctor = Doctor.objects.create(
            doctor_id="DOC-9001",
            name="Dr. Test Doctor",
            department=other,
            qualification="MBBS",
        )
        response = self.client.post(
            "/api/patients/",
            {
                "name": "Ward Mismatch",
                "phone": "+91 9847012345 (demo)",
                "department": self.department.id,
                "assigned_doctor": doctor.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("assigned_doctor", response.data["errors"])

    def test_stats_endpoint_counts_live_data(self):
        Patient.objects.create(
            patient_id="PAT-10001",
            name="Demo One",
            phone="+91 9847012345 (demo)",
            department=self.department,
            patient_type=Patient.PatientType.OPD,
        )
        Patient.objects.create(
            patient_id="PAT-10002",
            name="Demo Two",
            phone="+91 9847012346 (demo)",
            department=self.department,
            patient_type=Patient.PatientType.INPATIENT,
            admission_status=Patient.AdmissionStatus.ADMITTED,
        )
        response = self.client.get("/api/patients/stats/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["inpatients"], 1)
        self.assertEqual(response.data["admitted"], 1)

    def test_timeline_returns_registration_event(self):
        patient = Patient.objects.create(
            patient_id="PAT-10003",
            name="Demo Three",
            phone="+91 9847012347 (demo)",
            department=self.department,
        )
        response = self.client.get(f"/api/patients/{patient.id}/timeline/")
        self.assertEqual(response.status_code, 200)
        types = [event["type"] for event in response.data["events"]]
        self.assertIn("registration", types)


class PatientScopingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(name="General Medicine", code="GMED")
        self.own = Patient.objects.create(
            patient_id="PAT-20001", name="Own Record", phone="+91 9000000011 (demo)",
            department=self.department,
        )
        self.other = Patient.objects.create(
            patient_id="PAT-20002", name="Someone Else", phone="+91 9000000012 (demo)",
            department=self.department,
        )
        self.patient_user = User.objects.create_user(
            username="portal.patient",
            email="portal.patient@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.PATIENT,
        )
        self.own.user = self.patient_user
        self.own.save(update_fields=["user"])

    def test_patient_only_sees_their_own_record(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, 200)
        identifiers = [row["patient_id"] for row in response.data["results"]]
        self.assertEqual(identifiers, ["PAT-20001"])

    def test_patient_cannot_open_another_record(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(f"/api/patients/{self.other.id}/")
        self.assertEqual(response.status_code, 404)

    def test_patient_cannot_create_patients(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.post("/api/patients/", {"name": "Nope"}, format="json")
        self.assertEqual(response.status_code, 403)
