# Builders for stores, procurement, billing and insurance.

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from billing.models import Invoice, InvoiceItem
from insurance.models import InsuranceClaim, InsurancePolicy, InsuranceProvider
from inventory.models import InventoryItem, PurchaseOrder, PurchaseOrderItem, StockMovement, Supplier

from .catalogues import INSURANCE_PROVIDERS, INVENTORY_ITEMS, SUPPLIERS


def seed_suppliers():
    suppliers = {}
    for code, name, contact, phone, email, category, address in SUPPLIERS:
        supplier, _ = Supplier.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "contact_person": contact,
                "phone": "{} (demo)".format(phone),
                "email": email,
                "address": address,
                "category": category,
                "tax_id": "DEMO-{}-{:06d}".format(code, 100000),
                "payment_terms": "Net 30",
                "rating": Decimal("4.2"),
                "is_active": True,
                "is_demo": True,
            },
        )
        suppliers[category] = supplier
    suppliers["default"] = Supplier.objects.order_by("id").first()
    return suppliers


def seed_inventory(suppliers):
    today = date.today()
    created = 0
    for index, entry in enumerate(INVENTORY_ITEMS):
        name, category, unit, stock, reorder, price, location, expiry_days = entry
        supplier = suppliers.get(category) or suppliers.get("default")
        item = InventoryItem.objects.update_or_create(
            item_code="ITM-{}".format(1001 + index),
            defaults={
                "name": name,
                "category": category,
                "description": "{} (fictional demo stock item).".format(name),
                "unit": unit,
                "stock": stock,
                "reorder_level": reorder,
                "unit_price": price,
                "supplier": supplier,
                "location": location,
                "batch_number": "IB-{}-{:04d}".format(today.year, index + 1),
                "expiry_date": today + timedelta(days=expiry_days) if expiry_days else None,
                "last_restocked_at": timezone.now() - timedelta(days=index % 21),
            },
        )[0]
        item.status = item.compute_status()
        item.save(update_fields=["status"])
        created += 1

        StockMovement.objects.update_or_create(
            item=item,
            reference="OPENING-{}".format(item.item_code),
            defaults={
                "movement_type": StockMovement.MovementType.IN,
                "quantity": stock,
                "balance_after": stock,
                "reason": "Opening balance loaded with the demo dataset.",
            },
        )
    return created


def seed_purchase_orders(suppliers, rng):
    created = 0
    for index in range(1, 13):
        supplier = rng.choice(list(Supplier.objects.all()))
        order_date = date.today() - timedelta(days=rng.randint(0, 40))
        status = rng.choice(
            [
                PurchaseOrder.Status.DRAFT,
                PurchaseOrder.Status.SUBMITTED,
                PurchaseOrder.Status.APPROVED,
                PurchaseOrder.Status.PARTIALLY_RECEIVED,
                PurchaseOrder.Status.RECEIVED,
            ]
        )
        order, _ = PurchaseOrder.objects.update_or_create(
            po_number="PO-{}".format(1000 + index),
            defaults={
                "supplier": supplier,
                "order_date": order_date,
                "expected_date": order_date + timedelta(days=rng.randint(5, 21)),
                "status": status,
                "notes": "Demo purchase order for the AsterNova showcase.",
            },
        )
        order.items.all().delete()
        for _ in range(rng.randint(2, 4)):
            item = rng.choice(list(InventoryItem.objects.all()))
            quantity = rng.randint(5, 60)
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                item=item,
                description=item.name,
                quantity=quantity,
                received_quantity=quantity if status == PurchaseOrder.Status.RECEIVED else 0,
                unit_price=item.unit_price,
            )
        order.recalculate()
        created += 1
    return created


SERVICE_SEQUENCE = [
    InvoiceItem.ServiceType.CONSULTATION,
    InvoiceItem.ServiceType.LABORATORY,
    InvoiceItem.ServiceType.RADIOLOGY,
    InvoiceItem.ServiceType.PHARMACY,
    InvoiceItem.ServiceType.ROOM_CHARGE,
    InvoiceItem.ServiceType.SURGERY,
    InvoiceItem.ServiceType.PROCEDURE,
    InvoiceItem.ServiceType.NURSING,
    InvoiceItem.ServiceType.OTHER,
]


def _invoice_items_for(patient, rng):
    """Assemble a plausible bill from the patient's own clinical records."""
    items = []
    doctor = patient.assigned_doctor
    if doctor is not None:
        items.append(
            (
                InvoiceItem.ServiceType.CONSULTATION,
                "Consultation - {}".format(doctor.name),
                1,
                doctor.consultation_fee,
            )
        )

    for report in patient.lab_reports.select_related("test")[:2]:
        if report.test is not None:
            items.append(
                (
                    InvoiceItem.ServiceType.LABORATORY,
                    report.test.name,
                    1,
                    report.test.price,
                )
            )

    for study in patient.radiology_studies.all()[:1]:
        items.append(
            (
                InvoiceItem.ServiceType.RADIOLOGY,
                "{} - {}".format(study.get_scan_type_display(), study.body_part or ""),
                1,
                study.price,
            )
        )

    for prescription in patient.prescriptions.all()[:1]:
        for line in prescription.items.all()[:3]:
            if line.medicine is not None:
                items.append(
                    (
                        InvoiceItem.ServiceType.PHARMACY,
                        line.medicine.name,
                        line.quantity,
                        line.medicine.price,
                    )
                )

    admission = patient.admissions.first()
    if admission is not None:
        days = max(1, admission.length_of_stay)
        rate = admission.bed.daily_rate if admission.bed else Decimal("1500")
        items.append(
            (
                InvoiceItem.ServiceType.ROOM_CHARGE,
                "Room charges - {} day(s)".format(days),
                days,
                rate,
            )
        )

    surgery = patient.surgeries.filter(status="completed").first()
    if surgery is not None:
        items.append(
            (
                InvoiceItem.ServiceType.SURGERY,
                surgery.surgery_name,
                1,
                surgery.estimated_cost,
            )
        )

    if not items:
        items.append(
            (
                InvoiceItem.ServiceType.CONSULTATION,
                "General consultation",
                1,
                Decimal("500"),
            )
        )
    return items


def seed_invoices(patients, rng):
    created = 0
    counter = 1001

    for patient in patients:
        invoices = 2 if patient.patient_type in {"inpatient", "icu", "discharged"} else 1
        for _ in range(invoices):
            invoice_date = date.today() - timedelta(days=rng.randint(0, 35))
            payment_status = rng.choices(
                ["paid", "partially_paid", "pending"], weights=[58, 22, 20], k=1
            )[0]
            invoice, _ = Invoice.objects.update_or_create(
                invoice_number="INV-{}".format(counter),
                defaults={
                    "patient": patient,
                    "admission": patient.admissions.first(),
                    "doctor": patient.assigned_doctor,
                    "date": invoice_date,
                    "discount": rng.choice([0, 0, 100, 250, 500]),
                    "tax_rate": Decimal("5.00"),
                    "payment_method": rng.choice(
                        [
                            Invoice.PaymentMethod.CASH,
                            Invoice.PaymentMethod.CARD,
                            Invoice.PaymentMethod.UPI,
                            Invoice.PaymentMethod.INSURANCE,
                        ]
                    ),
                    "notes": "Demo invoice generated with the AsterNova dataset.",
                },
            )
            invoice.items.all().delete()
            for service_type, description, quantity, unit_price in _invoice_items_for(patient, rng):
                InvoiceItem.objects.create(
                    invoice=invoice,
                    service_type=service_type,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                )
            invoice.insurance_amount = (
                Decimal("0")
                if not patient.insurance_provider
                else (invoice.subtotal * Decimal("0.6")).quantize(Decimal("0.01"))
            )
            invoice.save(update_fields=["insurance_amount"])
            invoice.recalculate()

            payable = invoice.patient_payable
            if payment_status == "paid":
                invoice.paid_amount = payable
            elif payment_status == "partially_paid":
                invoice.paid_amount = (payable * Decimal("0.4")).quantize(Decimal("0.01"))
            else:
                invoice.paid_amount = Decimal("0")
            invoice._sync_payment_status()
            invoice.save(update_fields=["paid_amount", "payment_status"])
            counter += 1
            created += 1
    return created


def seed_insurance_providers():
    """Create (or refresh) the fictional insurers referenced by patients."""
    providers = {}
    for name, code, contact, phone, email in INSURANCE_PROVIDERS:
        provider, _ = InsuranceProvider.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "contact_person": contact,
                "phone": "{} (demo)".format(phone),
                "email": email,
                "address": "Demo corporate address, Kochi, Kerala",
                "claim_portal": "https://claims.{}.demo (fictional)".format(code.lower()),
                "is_demo": True,
            },
        )
        providers[code] = provider
    return providers


def seed_insurance(patients, rng):
    """Create patient policies and the claims raised against them."""
    providers = seed_insurance_providers()
    provider_list = list(providers.values())
    today = date.today()
    policies = 0
    claims = 0
    claim_counter = 1001

    for patient in patients:
        if not patient.insurance_policy_number:
            continue
        provider = rng.choice(provider_list)
        policy, _ = InsurancePolicy.objects.update_or_create(
            policy_number=patient.insurance_policy_number,
            defaults={
                "patient": patient,
                "provider": provider,
                "policy_type": rng.choice(
                    [
                        InsurancePolicy.PolicyType.INDIVIDUAL,
                        InsurancePolicy.PolicyType.FAMILY,
                        InsurancePolicy.PolicyType.CORPORATE,
                        InsurancePolicy.PolicyType.GOVERNMENT,
                    ]
                ),
                "coverage_amount": rng.choice([200000, 300000, 500000, 750000, 1000000]),
                "valid_from": today - timedelta(days=rng.randint(60, 900)),
                "valid_to": today + timedelta(days=rng.randint(30, 400)),
                "corporate_account": rng.choice(
                    ["", "Infopark Tech Park", "State Government Pool", "Demo Corporate"]
                ),
                "status": InsurancePolicy.Status.ACTIVE,
            },
        )
        policies += 1

        invoice = patient.invoices.first()
        if invoice is None or rng.random() > 0.62:
            continue
        claim_amount = invoice.patient_payable
        status = rng.choices(
            [
                "submitted",
                "under_review",
                "approved",
                "partially_approved",
                "rejected",
                "settled",
            ],
            weights=[20, 20, 18, 12, 10, 20],
            k=1,
        )[0]
        approved = Decimal("0")
        rejected = Decimal("0")
        if status in {"approved", "settled"}:
            approved = claim_amount
        elif status == "partially_approved":
            approved = (claim_amount * Decimal("0.7")).quantize(Decimal("0.01"))
            rejected = claim_amount - approved
        elif status == "rejected":
            rejected = claim_amount

        submitted = today - timedelta(days=rng.randint(1, 30))
        InsuranceClaim.objects.update_or_create(
            claim_number="CLM-{}".format(claim_counter),
            defaults={
                "policy": policy,
                "patient": patient,
                "invoice": invoice,
                "claim_amount": claim_amount,
                "approved_amount": approved,
                "rejected_amount": rejected,
                "status": status,
                "submitted_date": submitted,
                "reviewed_date": submitted + timedelta(days=rng.randint(2, 8))
                if status not in {"submitted"}
                else None,
                "settled_date": submitted + timedelta(days=rng.randint(10, 20))
                if status == "settled"
                else None,
                "diagnosis_code": "DEMO-{:03d}".format(rng.randint(1, 999)),
                "treatment_summary": "Hospitalisation and treatment as per discharge summary.",
                "rejection_reason": "Documentation incomplete (demo reason)."
                if status == "rejected"
                else "",
                "notes": "Fictional insurance claim created for the showcase.",
            },
        )
        claim_counter += 1
        claims += 1

    return {"providers": len(providers), "policies": policies, "claims": claims}
