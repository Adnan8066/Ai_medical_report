# Builders for wards, the 350 demo beds and the patient population.

from datetime import date, timedelta

from django.utils import timezone

from beds.models import Bed, Ward
from patients.models import Patient, Vitals

from .names import (
    ALLERGY_POOL,
    BLOOD_GROUPS,
    BLOOD_WEIGHTS,
    CHRONIC_POOL,
    CITIES,
    FEMALE_FIRST_NAMES,
    HISTORY_POOL,
    MALE_FIRST_NAMES,
    RELATIONS,
    STREETS,
    SURNAMES,
)

WARD_PLAN = [
    ("General Medicine Ward A", "WARD-GMA", "GMED", "general", "GMA", 60, "1st Floor", 1200),
    ("General Surgery Ward B", "WARD-GSB", "GSUR", "general", "GSB", 60, "1st Floor", 1300),
    ("Semi-Private Ward", "WARD-SPV", None, "semi_private", "SP", 60, "2nd Floor", 2800),
    ("Private Rooms", "WARD-PRV", None, "private", "P", 50, "3rd Floor", 4800),
    ("Intensive Care Unit", "WARD-ICU", "GMED", "icu", "ICU", 40, "2nd Floor", 9500),
    ("Emergency Ward", "WARD-EMR", "EMER", "emergency", "ER", 20, "Ground Floor", 2200),
    ("Pediatric Ward", "WARD-PED", "PEDI", "pediatric", "PED", 30, "2nd Floor", 1800),
    ("Maternity Ward", "WARD-MAT", "OBST", "maternity", "MAT", 20, "3rd Floor", 2600),
    ("Isolation Ward", "WARD-ISO", None, "isolation", "ISO", 10, "4th Floor", 5200),
]


def seed_beds(departments, rng, admitted_patients):
    """
    Create the full 350 bed inventory and mirror real occupancy.

    Occupied beds are linked to the inpatients created by ``seed_patients`` so
    the bed board and the admission list always agree.
    """
    # Beds are regenerated on every run so the numbering always matches the
    # ward plan; admissions are re-linked later in the same command.
    Bed.objects.all().delete()

    beds = []
    for name, code, department_code, category, prefix, count, floor, rate in WARD_PLAN:
        ward, _ = Ward.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "department": departments.get(department_code) if department_code else None,
                "floor": floor,
                "category": category,
                "description": "{} bed category at AsterNova (demo data).".format(
                    category.replace("_", " ").title()
                ),
                "is_active": True,
            },
        )
        for index in range(1, count + 1):
            number = "{}-{}".format(prefix, str(index).zfill(3))
            bed, _ = Bed.objects.update_or_create(
                bed_number=number,
                defaults={
                    "ward": ward,
                    "department": departments.get(department_code)
                    if department_code
                    else None,
                    "category": category,
                    "floor": floor,
                    "room_number": "{}".format(100 + index // 4),
                    "daily_rate": rate,
                    "has_oxygen": True,
                    "has_ventilator": category == "icu",
                    "is_monitored": category in {"icu", "emergency"},
                },
            )
            beds.append(bed)

    # Reserve a slice of beds for maintenance and cleaning -------------------
    maintenance = beds[::17]
    for bed in maintenance:
        bed.status = Bed.Status.MAINTENANCE

    # Distribute the inpatients across the non-ICU wards first --------------
    assignable = [
        bed
        for bed in beds
        if bed not in maintenance and bed.category not in {"icu", "emergency"}
    ]
    icu_beds = [bed for bed in beds if bed.category == "icu" and bed not in maintenance]
    emergency_beds = [
        bed for bed in beds if bed.category == "emergency" and bed not in maintenance
    ]

    icu_patients = [patient for patient in admitted_patients if patient.patient_type == "icu"]
    emergency_patients = [
        patient for patient in admitted_patients if patient.patient_type == "emergency"
    ]
    ward_patients = [
        patient
        for patient in admitted_patients
        if patient.patient_type not in {"icu", "emergency"}
    ]

    def place(pool, targets, patient_list):
        for bed, patient in zip(targets, patient_list):
            bed.patient = patient
            bed.status = Bed.Status.OCCUPIED
            pool.append((bed, patient))

    rng.shuffle(assignable)
    rng.shuffle(icu_beds)
    rng.shuffle(emergency_beds)
    rng.shuffle(ward_patients)
    rng.shuffle(icu_patients)
    rng.shuffle(emergency_patients)

    occupied = []
    place(occupied, icu_beds, icu_patients)
    place(occupied, emergency_beds, emergency_patients)
    place(occupied, assignable, ward_patients)

    reserved_index = len(occupied)

    for bed in beds:
        if bed in maintenance or bed.patient_id:
            continue
        bed.status = Bed.Status.AVAILABLE

    # A handful of available beds are reserved for incoming transfers -------
    available = [bed for bed in beds if bed.status == Bed.Status.AVAILABLE]
    for bed in available[: max(1, len(available) // 12)]:
        bed.status = Bed.Status.RESERVED

    for bed in beds:
        bed.save(
            update_fields=["patient", "status", "ward", "department", "updated_at"]
        )

    return {"beds": len(beds), "occupied": len(occupied), "reserved_index": reserved_index}


PATIENT_MIX = [
    ("inpatient", 210),
    ("opd", 90),
    ("discharged", 60),
    ("scheduled", 40),
    ("icu", 30),
    ("follow_up", 30),
    ("emergency", 18),
]


def seed_patients(departments, doctors_by_code, rng, insurance_providers):
    """Create the fictional patient population that fills every module."""
    used_names = set()
    patients = []
    counter = 10001
    today = date.today()

    department_list = list(departments.values())
    type_pool = []
    for patient_type, count in PATIENT_MIX:
        type_pool.extend([patient_type] * count)
    rng.shuffle(type_pool)

    for patient_type in type_pool:
        department = rng.choice(department_list)
        doctors = doctors_by_code.get(department.code) or []
        doctor = rng.choice(doctors) if doctors else None

        for _ in range(400):
            pool = MALE_FIRST_NAMES if rng.random() < 0.5 else FEMALE_FIRST_NAMES
            name = "{} {}".format(rng.choice(pool), rng.choice(SURNAMES))
            if name not in used_names:
                used_names.add(name)
                break
        else:
            name = "Demo Patient {}".format(counter)
            used_names.add(name)

        gender = "female" if name.split()[0] in FEMALE_FIRST_NAMES else "male"
        age = rng.randint(1, 88)
        dob = today - timedelta(days=age * 365 + rng.randint(0, 360))
        registration = today - timedelta(days=rng.randint(0, 420))

        if patient_type == "inpatient":
            status = rng.choice(["admitted", "under_treatment", "stable"])
            admission_status = "admitted"
        elif patient_type == "icu":
            status = rng.choice(["critical", "under_treatment", "stable"])
            admission_status = "admitted"
        elif patient_type == "emergency":
            status = rng.choice(["critical", "under_treatment", "waiting"])
            admission_status = rng.choice(["admitted", "not_admitted"])
        elif patient_type == "discharged":
            status = "discharged"
            admission_status = "discharged"
        elif patient_type == "follow_up":
            status = "follow_up"
            admission_status = "not_admitted"
        elif patient_type == "scheduled":
            status = "registered"
            admission_status = "not_admitted"
        else:
            status = rng.choice(["registered", "waiting", "in_consultation"])
            admission_status = "not_admitted"

        has_insurance = rng.random() < 0.68
        provider = rng.choice(insurance_providers) if has_insurance and insurance_providers else None
        city = rng.choice(CITIES)

        patient, _ = Patient.objects.update_or_create(
            patient_id="PAT-{}".format(counter),
            defaults={
                "name": name,
                "date_of_birth": dob,
                "gender": gender,
                "blood_group": rng.choices(BLOOD_GROUPS, weights=BLOOD_WEIGHTS, k=1)[0],
                "phone": "+91 9{} (demo)".format(rng.randint(100000000, 999999999)),
                "email": "patient{}@example-demo.invalid".format(counter),
                "address": "{}, {}".format(rng.randint(1, 240), rng.choice(STREETS)),
                "city": city,
                "state": "Kerala",
                "postal_code": "682{:03d}".format(rng.randint(1, 80)),
                "emergency_contact_name": "{} {}".format(
                    rng.choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES),
                    rng.choice(SURNAMES),
                ),
                "emergency_contact_phone": "+91 9{} (demo)".format(
                    rng.randint(100000000, 999999999)
                ),
                "emergency_contact_relation": rng.choice(RELATIONS),
                "department": department,
                "assigned_doctor": doctor,
                "registration_date": registration,
                "patient_type": patient_type,
                "current_status": status,
                "admission_status": admission_status,
                "allergies": ", ".join(
                    rng.sample(ALLERGY_POOL, k=rng.randint(1, 2))
                ),
                "medical_history": rng.choice(HISTORY_POOL),
                "chronic_conditions": rng.choice(CHRONIC_POOL),
                "height_cm": rng.randint(140, 188),
                "weight_kg": rng.randint(38, 96),
                "insurance_provider": provider["name"] if provider else "",
                "insurance_policy_number": "POL-{}-{:06d}".format(
                    provider["code"], rng.randint(1, 999999)
                )
                if provider
                else "",
                "notes": "Fictional demo record generated for the AsterNova showcase.",
            },
        )
        patients.append(patient)
        counter += 1

    return patients


def seed_vitals(patients, rng, staff_users):
    """Record a few observations for admitted patients and one for OPD patients."""
    created = 0
    base = timezone.localtime().replace(minute=0, second=0, microsecond=0)
    for patient in patients:
        readings = 4 if patient.patient_type in {"inpatient", "icu"} else 1
        for index in range(readings):
            # Deterministic timestamps keep repeat runs idempotent.
            recorded_at = base - timedelta(days=index, hours=6 * (index % 4) + 1)
            temperature = round(rng.uniform(36.2, 38.9), 1)
            pulse = rng.randint(58, 118)
            systolic = rng.randint(96, 158)
            diastolic = rng.randint(62, 96)
            spo2 = rng.randint(88, 100)
            status = "normal"
            if temperature >= 37.8 or pulse >= 100 or spo2 < 95 or systolic >= 140:
                status = "abnormal"
            if spo2 < 90 or temperature >= 39.5 or systolic >= 180:
                status = "critical"
            Vitals.objects.update_or_create(
                patient=patient,
                recorded_at=recorded_at,
                defaults={
                    "recorded_by": rng.choice(staff_users) if staff_users else None,
                    "temperature_c": temperature,
                    "pulse_bpm": pulse,
                    "respiratory_rate": rng.randint(12, 24),
                    "bp_systolic": systolic,
                    "bp_diastolic": diastolic,
                    "spo2": spo2,
                    "blood_glucose": rng.randint(80, 220),
                    "pain_score": rng.randint(0, 8),
                    "status": status,
                    "notes": "Demo observation recorded by nursing staff.",
                },
            )
            created += 1
    return created
