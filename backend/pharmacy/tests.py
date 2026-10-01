"""Prescription dispensing, stock decrement and invoice recalculation tests."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from billing.models import Invoice, InvoiceItem
from patients.models import Patient
from users.models import RoleCode, User

from .models import Medicine, Prescription, PrescriptionItem


class DispensingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.pharmacist = User.objects.create_user(
            username="rx.pharmacist",
            email="rx.pharmacist@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.PHARMACIST,
        )
        self.patient = Patient.objects.create(
            patient_id="PAT-50001", name="Dispense Patient", phone="+91 9000000041 (demo)"
        )
        self.medicine = Medicine.objects.create(
            medicine_id="MED-95001",
            name="Paracetamol 500 mg",
            category="analgesic",
            stock=100,
            reorder_level=20,
            price=Decimal("2.50"),
        )
        self.prescription = Prescription.objects.create(
            prescription_id="RX-95001", patient=self.patient, date=date.today()
        )
        PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=self.medicine,
            medicine_name=self.medicine.name,
            quantity=10,
        )
        self.client.force_authenticate(self.pharmacist)

    def test_dispensing_decrements_stock_and_marks_the_prescription(self):
        response = self.client.post(f"/api/pharmacy/prescriptions/{self.prescription.id}/dispense/")
        self.assertEqual(response.status_code, 200, response.data)
        self.medicine.refresh_from_db()
        self.prescription.refresh_from_db()
        self.assertEqual(self.medicine.stock, 90)
        self.assertEqual(self.prescription.status, Prescription.Status.DISPENSED)
        self.assertTrue(self.prescription.items.first().dispensed)

    def test_dispensing_without_stock_is_rejected_and_leaves_stock_untouched(self):
        self.medicine.stock = 3
        self.medicine.save(update_fields=["stock"])
        response = self.client.post(f"/api/pharmacy/prescriptions/{self.prescription.id}/dispense/")
        self.assertEqual(response.status_code, 400)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock, 3)
        self.assertFalse(self.prescription.items.first().dispensed)

    def test_medicine_status_recomputes_from_stock(self):
        self.medicine.stock = 10
        self.medicine.status = self.medicine.compute_status()
        self.medicine.save(update_fields=["stock", "status"])
        self.assertEqual(self.medicine.status, Medicine.Status.LOW_STOCK)
        self.medicine.stock = 0
        self.assertEqual(self.medicine.compute_status(), Medicine.Status.OUT_OF_STOCK)

    def test_stock_adjustment_endpoint_applies_a_movement(self):
        response = self.client.post(
            f"/api/pharmacy/medicines/{self.medicine.id}/adjust_stock/",
            {"quantity": -25},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stock"], 75)


class InvoiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.billing = User.objects.create_user(
            username="bill.staff",
            email="bill.staff@asternova.demo",
            password="DemoPass!234",
            role=RoleCode.BILLING_STAFF,
        )
        self.patient = Patient.objects.create(
            patient_id="PAT-50002", name="Invoice Patient", phone="+91 9000000042 (demo)"
        )
        self.client.force_authenticate(self.billing)

    def _invoice(self):
        return Invoice.objects.create(
            invoice_number="INV-95001",
            patient=self.patient,
            date=date.today(),
            discount=Decimal("100"),
            tax_rate=Decimal("5.00"),
            insurance_amount=Decimal("500"),
        )

    def test_recalculation_applies_discount_tax_and_insurance(self):
        invoice = self._invoice()
        InvoiceItem.objects.create(
            invoice=invoice, description="Consultation", quantity=1, unit_price=Decimal("2000")
        )
        InvoiceItem.objects.create(
            invoice=invoice, description="Laboratory", quantity=2, unit_price=Decimal("250")
        )
        invoice.recalculate()
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal("2500"))
        self.assertEqual(invoice.tax_amount, Decimal("120.00"))
        self.assertEqual(invoice.patient_payable, Decimal("2020.00"))

    def test_recording_a_partial_payment_sets_partially_paid(self):
        invoice = self._invoice()
        InvoiceItem.objects.create(
            invoice=invoice, description="Consultation", quantity=1, unit_price=Decimal("2000")
        )
        invoice.recalculate()
        response = self.client.post(
            f"/api/billing/{invoice.id}/record_payment/",
            {"amount": "500", "payment_method": "card"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["payment_status"], Invoice.PaymentStatus.PARTIALLY_PAID)

    def test_full_payment_marks_the_invoice_paid(self):
        invoice = self._invoice()
        InvoiceItem.objects.create(
            invoice=invoice, description="Consultation", quantity=1, unit_price=Decimal("2000")
        )
        invoice.recalculate()
        response = self.client.post(
            f"/api/billing/{invoice.id}/record_payment/",
            {"amount": str(invoice.patient_payable)},
            format="json",
        )
        self.assertEqual(response.data["payment_status"], Invoice.PaymentStatus.PAID)
        self.assertEqual(Decimal(response.data["balance_due"]), Decimal("0.00"))

    def test_zero_payment_is_rejected(self):
        invoice = self._invoice()
        response = self.client.post(
            f"/api/billing/{invoice.id}/record_payment/", {"amount": "0"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
