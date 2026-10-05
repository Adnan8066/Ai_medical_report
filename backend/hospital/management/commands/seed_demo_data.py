"""
Seed the AsterNova demonstration dataset.

    python manage.py seed_demo_data

The command is safe to run repeatedly: every record is written with
``update_or_create`` against a stable business key, so no duplicates appear.
Every patient, clinician, insurer and manufacturer in the dataset is fictional.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from documents.models import MedicalDocument
from hospital.demodata.catalogues import INSURANCE_PROVIDERS
from hospital.demodata import builders_core, builders_documents, builders_finance
from hospital.demodata import builders_diagnostics, builders_flow, builders_pharmacy
from hospital.demodata import builders_staff, builders_ward
from insurance.models import InsuranceProvider
from notifications.models import Notification
from users.models import Role, RoleCode, User


class Command(BaseCommand):
    help = "Create or refresh the fictional AsterNova hospital demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=20240928,
            help="Random seed for repeatable generation (default: 20240928).",
        )
        parser.add_argument(
            "--skip-documents",
            action="store_true",
            help="Skip PDF generation and the OCR/AI pipeline (faster).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing demo hospitals, users, patients and documents first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])
        summary = {}

        if options["reset"]:
            self._reset()

        summary.update(builders_core.seed_roles())
        builders_core.seed_hospital()
        summary["shifts"] = builders_core.seed_shifts()
        departments = builders_core.seed_departments()
        summary["departments"] = len(departments)

        doctors_by_code = builders_core.seed_doctors(departments, rng)
        summary["doctors"] = sum(len(items) for items in doctors_by_code.values())
        summary["staff"] = builders_staff.seed_staff(departments, rng)

        suppliers = builders_finance.seed_suppliers()
        summary["inventory_items"] = builders_finance.seed_inventory(suppliers)
        summary["purchase_orders"] = builders_finance.seed_purchase_orders(suppliers, rng)
        summary["lab_tests"] = builders_diagnostics.seed_lab_tests()

        builders_finance.seed_insurance_providers()
        providers = [
            {"name": name, "code": code}
            for name, code, *_ in INSURANCE_PROVIDERS
        ]

        patients = builders_ward.seed_patients(departments, doctors_by_code, rng, providers)
        summary["patients"] = len(patients)

        admitted = [p for p in patients if p.admission_status == "admitted"]
        bed_summary = builders_ward.seed_beds(departments, rng, admitted)
        summary["beds"] = bed_summary["beds"]
        summary["beds_occupied"] = bed_summary["occupied"]

        summary["appointments"] = builders_flow.seed_appointments(patients, doctors_by_code, rng)
        summary["opd_visits"] = builders_flow.seed_opd_visits(patients, rng)
        summary["emergency_cases"] = builders_flow.seed_emergency(
            departments, doctors_by_code, patients, rng
        )
        summary["admissions"] = builders_flow.seed_admissions(patients, rng)
        summary["nurse_assignments"] = builders_flow.seed_nurse_assignments(
            patients, departments, rng
        )

        nurse_users = list(User.objects.filter(role=RoleCode.NURSE))
        summary["vitals"] = builders_ward.seed_vitals(patients, rng, nurse_users)

        summary["lab_reports"] = builders_diagnostics.seed_lab_reports(patients, rng)
        summary["radiology_reports"] = builders_diagnostics.seed_radiology(patients, rng)

        summary["medicines"] = builders_pharmacy.seed_medicines(
            {category: supplier for category, supplier in suppliers.items()}
        )
        summary["prescriptions"] = builders_pharmacy.seed_prescriptions(patients, rng)
        summary["surgeries"] = builders_pharmacy.seed_surgeries(
            patients, departments, doctors_by_code, rng
        )
        summary.update(builders_pharmacy.seed_bloodbank(patients, rng))

        summary["invoices"] = builders_finance.seed_invoices(patients, rng)
        summary.update(builders_finance.seed_insurance(patients, rng))
        summary["discharge_summaries"] = builders_flow.seed_discharge_summaries(patients, rng)

        users_by_username = {
            user.username: user for user in User.objects.filter(is_demo=True)
        }
        summary.update(
            builders_staff.seed_users(departments, doctors_by_code, patients)
        )

        if not options["skip_documents"]:
            summary.update(builders_documents.seed_documents(patients, rng))
        else:
            summary["documents"] = MedicalDocument.objects.count()

        summary["notifications"] = builders_documents.seed_notifications(
            users_by_username, rng
        )
        summary["shift_assignments"] = builders_documents.seed_shift_assignments(rng)
        summary["audit_logs"] = builders_documents.seed_audit_logs(users_by_username, rng)

        self._report(summary)

    def _reset(self):
        """Remove the previously generated demo dataset (demo data only)."""
        from insurance.models import InsuranceClaim, InsurancePolicy
        from patients.models import Patient

        self.stdout.write(self.style.WARNING("Resetting existing demo data..."))

        # Claims and policies are PROTECTed, so they must go before the
        # patients they reference - deleting a patient first would cascade
        # into a policy and abort the whole reset.
        InsuranceClaim.objects.all().delete()
        InsurancePolicy.objects.all().delete()
        Patient.objects.all().delete()
        MedicalDocument.objects.all().delete()
        Notification.objects.all().delete()
        InsuranceProvider.objects.all().delete()
        Role.objects.all().delete()
        User.objects.filter(is_demo=True).delete()

    def _report(self, summary):
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("AsterNova demo dataset is ready (all data is fictional).")
        )
        self.stdout.write("-" * 58)
        for key in sorted(summary):
            value = summary[key]
            if isinstance(value, dict):
                value = ", ".join("{}={}".format(k, v) for k, v in value.items())
            self.stdout.write("{:<22} {}".format(key.replace("_", " ").title(), value))
        self.stdout.write("-" * 58)
        self.stdout.write(
            "Demo logins: admin@asternova.demo / doctor@asternova.demo / "
            "nurse@asternova.demo / reception@asternova.demo / patient@asternova.demo"
        )
        self.stdout.write(
            "Password: the value of DEMO_PASSWORD in your .env file "
            "(default AsterNova@2024)."
        )
