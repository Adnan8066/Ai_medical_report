# Builders for pharmacy stock, prescriptions, surgery and the blood bank.

from datetime import date, timedelta

from django.utils import timezone

from bloodbank.models import BLOOD_GROUPS, BloodIssue, BloodStock, Donation
from pharmacy.models import Medicine, Prescription, PrescriptionItem
from surgery.models import Surgery

from .catalogues import MEDICINES
from .names import (
    DEFAULT_SURGERY,
    FEMALE_FIRST_NAMES,
    MALE_FIRST_NAMES,
    SURGERY_NAMES,
    SURNAMES,
)


def seed_medicines(suppliers_by_category):
    """Create the pharmacy inventory with a realistic spread of stock states."""
    today = date.today()
    for index, entry in enumerate(MEDICINES):
        (
            name,
            generic,
            category,
            manufacturer,
            unit,
            price,
            cost,
            stock,
            reorder,
            expiry_days,
            prescription_required,
        ) = entry
        # The last three items are deliberately near expiry for the alert demo.
        if index >= len(MEDICINES) - 3:
            expiry_days = min(expiry_days, 45)
        supplier = suppliers_by_category.get(category) or suppliers_by_category.get("default")
        medicine = Medicine.objects.update_or_create(
            medicine_id="MED-{}".format(1001 + index),
            defaults={
                "name": name,
                "generic_name": generic,
                "category": category,
                "manufacturer": manufacturer,
                "batch_number": "BATCH-{}-{:04d}".format(today.year, index + 1),
                "expiry_date": today + timedelta(days=expiry_days),
                "stock": stock,
                "reorder_level": reorder,
                "unit": unit,
                "price": price,
                "cost_price": cost,
                "storage": "Room temperature" if category != "vaccine" else "Cold chain 2-8 C",
                "prescription_required": prescription_required,
                "supplier": supplier,
            },
        )[0]
        medicine.status = medicine.compute_status()
        medicine.save(update_fields=["status"])
    return Medicine.objects.count()


def seed_prescriptions(patients, rng):
    """Create prescriptions with dispensed and pending line items."""
    created = 0
    counter = 1001
    medicines = list(Medicine.objects.all())
    if not medicines:
        return 0

    for patient in patients:
        prescriptions = 2 if patient.patient_type in {"inpatient", "icu", "discharged"} else 1
        for _ in range(prescriptions):
            prescription, _ = Prescription.objects.update_or_create(
                prescription_id="RX-{}".format(counter),
                defaults={
                    "patient": patient,
                    "doctor": patient.assigned_doctor,
                    "admission": patient.admissions.first()
                    if patient.admission_status == "admitted"
                    else None,
                    "date": date.today() - timedelta(days=rng.randint(0, 20)),
                    "status": rng.choice(
                        [
                            Prescription.Status.PENDING,
                            Prescription.Status.DISPENSED,
                            Prescription.Status.DISPENSED,
                            Prescription.Status.PARTIALLY_DISPENSED,
                        ]
                    ),
                    "notes": "Demo prescription created for the AsterNova showcase.",
                },
            )
            prescription.items.all().delete()
            dispensed = prescription.status == Prescription.Status.DISPENSED
            for _ in range(rng.randint(1, 4)):
                medicine = rng.choice(medicines)
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medicine=medicine,
                    medicine_name=medicine.name,
                    dosage="1 {}".format(medicine.unit),
                    frequency=rng.choice(["Once daily", "Twice daily", "Thrice daily", "SOS"]),
                    duration=rng.choice(["3 days", "5 days", "7 days", "10 days"]),
                    route=rng.choice(["Oral", "Oral", "Intravenous", "Topical"]),
                    quantity=rng.randint(1, 3) * 5,
                    instructions="After food unless directed otherwise (demo).",
                    dispensed=dispensed,
                )
            counter += 1
            created += 1
    return created


def seed_surgeries(patients, departments, doctors_by_code, rng):
    """Schedule operations across the theatre complex."""
    from staff.models import Staff

    created = 0
    counter = 1001
    today = date.today()
    theatre_nurses = list(
        Staff.objects.filter(role=Staff.Role.NURSE).select_related("department")
    )
    surgical_departments = [
        code for code in doctors_by_code if code in SURGERY_NAMES
    ] or ["GSUR", "ORTH"]

    candidates = [
        patient
        for patient in patients
        if patient.patient_type in {"inpatient", "icu", "opd", "scheduled"}
    ]
    rng.shuffle(candidates)

    for patient in candidates[:140]:
        department_code = rng.choice(surgical_departments)
        department = departments.get(department_code)
        surgeons = doctors_by_code.get(department_code, [])
        if not surgeons or department is None:
            continue
        offset = rng.randint(-20, 12)
        surgery_date = today + timedelta(days=offset)
        if offset < 0:
            status = rng.choice(
                [Surgery.Status.COMPLETED, Surgery.Status.COMPLETED, Surgery.Status.CANCELLED]
            )
        elif offset == 0:
            status = rng.choice(
                [
                    Surgery.Status.PREPARING,
                    Surgery.Status.IN_PROGRESS,
                    Surgery.Status.SCHEDULED,
                ]
            )
        else:
            status = Surgery.Status.SCHEDULED

        start_hour = rng.randint(8, 16)
        start_time = timezone.datetime(
            surgery_date.year, surgery_date.month, surgery_date.day, start_hour, 0
        ).time()
        duration = rng.choice([45, 60, 90, 120, 180])
        end_time = (
            timezone.datetime.combine(surgery_date, start_time)
            + timedelta(minutes=duration)
        ).time()
        names = SURGERY_NAMES.get(department.name, DEFAULT_SURGERY)

        surgery, _ = Surgery.objects.update_or_create(
            surgery_id="SUR-{}".format(counter),
            defaults={
                "patient": patient,
                "surgeon": rng.choice(surgeons),
                "department": department,
                "surgery_name": rng.choice(names),
                "procedure_code": "PR-{:04d}".format(rng.randint(1, 9999)),
                "ot_room": "OT-{}".format(rng.randint(1, 6)),
                "date": surgery_date,
                "start_time": start_time,
                "end_time": end_time,
                "estimated_duration_minutes": duration,
                "anesthetist": rng.choice(doctors_by_code.get("ANES", []) or [None]),
                "anesthesia_type": rng.choice(
                    [
                        Surgery.AnesthesiaType.GENERAL,
                        Surgery.AnesthesiaType.SPINAL,
                        Surgery.AnesthesiaType.REGIONAL,
                        Surgery.AnesthesiaType.SEDATION,
                    ]
                ),
                "status": status,
                "blood_units_reserved": rng.choice([0, 0, 1, 2]),
                "pre_op_notes": "Demo pre-operative checklist completed and signed.",
                "post_op_notes": "Demo post-operative note." if offset < 0 else "",
                "estimated_cost": rng.choice([25000, 45000, 68000, 125000, 210000]),
            },
        )
        if theatre_nurses:
            surgery.nurses.set(rng.sample(theatre_nurses, k=min(2, len(theatre_nurses))))
        counter += 1
        created += 1
    return created


BLOOD_LEVELS = {
    "A+": (26, 4),
    "A-": (4, 1),
    "B+": (32, 6),
    "B-": (3, 0),
    "AB+": (12, 2),
    "AB-": (2, 0),
    "O+": (38, 7),
    "O-": (5, 1),
}


def seed_bloodbank(patients, rng):
    """Create stock levels, donation records and issue records."""
    for group in BLOOD_GROUPS:
        available, reserved = BLOOD_LEVELS.get(group, (10, 2))
        BloodStock.objects.update_or_create(
            blood_group=group,
            defaults={
                "units_available": available,
                "units_reserved": reserved,
                "critical_threshold": 5,
            },
        )

    for index in range(1, 61):
        pool = MALE_FIRST_NAMES if rng.random() < 0.6 else FEMALE_FIRST_NAMES
        donation_date = date.today() - timedelta(days=rng.randint(0, 90))
        screening = rng.choices(
            ["passed", "pending", "failed"], weights=[85, 10, 5], k=1
        )[0]
        Donation.objects.update_or_create(
            donation_id="DON-{}".format(1000 + index),
            defaults={
                "donor_name": "{} {}".format(rng.choice(pool), rng.choice(SURNAMES)),
                "donor_code": "DNR-{:05d}".format(index),
                "blood_group": rng.choice(BLOOD_GROUPS),
                "units": rng.choice([1, 1, 1, 2]),
                "donation_date": donation_date,
                "donor_age": rng.randint(19, 58),
                "donor_gender": "female" if pool is FEMALE_FIRST_NAMES else "male",
                "donor_phone": "+91 9{} (demo)".format(rng.randint(100000000, 999999999)),
                "camp_location": rng.choice(
                    [
                        "In-hospital donation camp",
                        "Community camp - Kakkanad",
                        "Corporate camp - Infopark",
                        "College camp - Edappally",
                    ]
                ),
                "screening": screening,
                "hemoglobin": round(rng.uniform(12.0, 16.5), 1),
                "notes": "Fictional donation record for demonstration.",
            },
        )

    candidates = [
        patient for patient in patients if patient.patient_type in {"inpatient", "icu", "emergency"}
    ]
    rng.shuffle(candidates)
    for index, patient in enumerate(candidates[:45]):
        requested = timezone.now() - timedelta(
            days=rng.randint(0, 25), hours=rng.randint(0, 20)
        )
        status = rng.choices(
            ["reserved", "issued", "transfused", "returned"],
            weights=[25, 40, 25, 10],
            k=1,
        )[0]
        BloodIssue.objects.update_or_create(
            issue_id="BIS-{}".format(1000 + index),
            defaults={
                "blood_group": patient.blood_group or rng.choice(BLOOD_GROUPS),
                "units": rng.choice([1, 1, 2, 2, 3]),
                "patient": patient,
                "ward": patient.current_beds.first().ward.name
                if patient.current_beds.exists()
                and patient.current_beds.first().ward is not None
                else "Emergency Ward",
                "reason": rng.choice(
                    [
                        "Anaemia correction",
                        "Pre-operative preparation",
                        "Post-partum haemorrhage",
                        "Trauma resuscitation",
                    ]
                ),
                "crossmatch_id": "XM-{:06d}".format(rng.randint(1, 999999)),
                "requested_at": requested,
                "issued_at": requested + timedelta(minutes=rng.randint(20, 300))
                if status != "reserved"
                else None,
                "status": status,
                "notes": "Demo blood bank transaction.",
            },
        )
    return {
        "stock": BloodStock.objects.count(),
        "donations": Donation.objects.count(),
        "issues": BloodIssue.objects.count(),
    }
