"""Invoices and invoice line items."""

from decimal import Decimal

from django.conf import settings
from django.db import models


class Invoice(models.Model):
    class PaymentStatus(models.TextChoices):
        PAID = "paid", "Paid"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        PENDING = "pending", "Pending"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        UPI = "upi", "UPI"
        NET_BANKING = "net_banking", "Net Banking"
        INSURANCE = "insurance", "Insurance"
        PENDING = "pending", "Not Paid"

    invoice_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="invoices"
    )
    admission = models.ForeignKey(
        "admissions.Admission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices",
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices",
    )
    date = models.DateField(db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    patient_payable = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.PENDING
    )
    notes = models.CharField(max_length=250, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices_created",
    )
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["payment_status"]), models.Index(fields=["date"])]

    def __str__(self):
        return f"{self.invoice_number} - {self.patient.name}"

    @property
    def balance_due(self):
        return (self.patient_payable or 0) - (self.paid_amount or 0)

    def recalculate(self, save=True):
        """Recompute every derived amount from the line items."""
        subtotal = sum((item.amount or Decimal("0")) for item in self.items.all())
        self.subtotal = subtotal
        taxable = max(Decimal("0"), subtotal - (self.discount or Decimal("0")))
        self.tax_amount = (taxable * (self.tax_rate or Decimal("0")) / Decimal("100")).quantize(
            Decimal("0.01")
        )
        total = taxable + self.tax_amount
        self.patient_payable = max(
            Decimal("0"), total - (self.insurance_amount or Decimal("0"))
        )
        self._sync_payment_status()
        if save:
            self.save()
        return self.patient_payable

    def _sync_payment_status(self):
        if self.payment_status == self.PaymentStatus.CANCELLED:
            return
        if self.paid_amount >= self.patient_payable and self.patient_payable > 0:
            self.payment_status = self.PaymentStatus.PAID
        elif self.paid_amount > 0:
            self.payment_status = self.PaymentStatus.PARTIALLY_PAID
        else:
            self.payment_status = self.PaymentStatus.PENDING


class InvoiceItem(models.Model):
    class ServiceType(models.TextChoices):
        CONSULTATION = "consultation", "Consultation"
        LABORATORY = "laboratory", "Laboratory"
        RADIOLOGY = "radiology", "Radiology"
        PHARMACY = "pharmacy", "Pharmacy"
        ROOM_CHARGE = "room_charge", "Room Charges"
        SURGERY = "surgery", "Surgery"
        PROCEDURE = "procedure", "Procedure"
        NURSING = "nursing", "Nursing Care"
        OTHER = "other", "Other Services"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    service_type = models.CharField(
        max_length=20, choices=ServiceType.choices, default=ServiceType.CONSULTATION
    )
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.amount = (self.unit_price or Decimal("0")) * (self.quantity or 0)
        super().save(*args, **kwargs)
