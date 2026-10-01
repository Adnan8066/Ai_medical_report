# Builders for the wider workforce and the demo login accounts.

from datetime import date, timedelta

from django.conf import settings

from staff.models import Shift, Staff
from users.models import Role, RoleCode, User

from .builders_core import DEMO_ACCOUNTS
from .names import FEMALE_FIRST_NAMES, MALE_FIRST_NAMES, SURNAMES


def name_factory(rng, used):
    counter = {"value": 0}

    def make():
        for _ in range(300):
            pool = FEMALE_FIRST_NAMES if rng.random() < 0.6 else MALE_FIRST_NAMES
            name = "{} {}".format(rng.choice(pool), rng.choice(SURNAMES))
            if name not in used:
                used.add(name)
                return name
        counter["value"] += 1
        return "Demo Staff {}".format(counter["value"])

    return make


def seed_staff(departments, rng):
    """Create nurses, technicians, pharmacists and support staff."""
    shifts = list(Shift.objects.all())
    used_names = set()
    make_name = name_factory(rng, used_names)
    counter = 2001
    created = 0

    ward_plan = [
        (Staff.Role.NURSE, "Staff Nurse", 3),
        (Staff.Role.NURSE, "Senior Staff Nurse", 1),
        (Staff.Role.RECEPTIONIST, "Front Office Executive", 1),
        (Staff.Role.HOUSEKEEPING, "Housekeeping Associate", 1),
    ]

    for entry in departments.values():
        for role, designation, count in ward_plan:
            for _ in range(count):
                employee_id = "EMP-{}".format(counter)
                counter += 1
                Staff.objects.update_or_create(
                    employee_id=employee_id,
                    defaults={
                        "name": make_name(),
                        "gender": "female" if rng.random() < 0.7 else "male",
                        "department": entry,
                        "role": role,
                        "designation": designation,
                        "joining_date": date.today() - timedelta(days=365 * rng.randint(1, 12)),
                        "shift": rng.choice(shifts) if shifts else None,
                        "contact": "+91 9{} (demo)".format(rng.randint(100000000, 999999999)),
                        "email": "{}@asternova.demo".format(employee_id.lower()),
                        "address": "Demo address, Kochi, Kerala",
                        "qualification": "GNM" if role == Staff.Role.NURSE else "",
                        "status": rng.choice(
                            [Staff.Status.ACTIVE, Staff.Status.ON_DUTY, Staff.Status.ACTIVE]
                        ),
                    },
                )
                created += 1

    specialist_plan = [
        (Staff.Role.PHARMACIST, "Clinical Pharmacist", "GMED", 3),
        (Staff.Role.LABORATORY, "Laboratory Technician", "PATH", 5),
        (Staff.Role.RADIOLOGY, "Radiology Technician", "RADI", 4),
        (Staff.Role.TECHNICIAN, "OT Technician", "ANES", 4),
        (Staff.Role.BILLING, "Billing Executive", "GMED", 3),
        (Staff.Role.ADMINISTRATOR, "Hospital Administrator", "GMED", 3),
        (Staff.Role.SECURITY, "Security Officer", "GMED", 5),
        (Staff.Role.HOUSEKEEPING, "Housekeeping Supervisor", "GMED", 3),
        (Staff.Role.TECHNICIAN, "Biomedical Engineer", "RADI", 2),
    ]
    for role, designation, department_code, count in specialist_plan:
        for _ in range(count):
            employee_id = "EMP-{}".format(counter)
            counter += 1
            Staff.objects.update_or_create(
                employee_id=employee_id,
                defaults={
                    "name": make_name(),
                    "gender": "female" if rng.random() < 0.55 else "male",
                    "department": departments[department_code],
                    "role": role,
                    "designation": designation,
                    "joining_date": date.today() - timedelta(days=365 * rng.randint(1, 14)),
                    "shift": rng.choice(shifts) if shifts else None,
                    "contact": "+91 9{} (demo)".format(rng.randint(100000000, 999999999)),
                    "email": "{}@asternova.demo".format(employee_id.lower()),
                    "status": Staff.Status.ACTIVE,
                },
            )
            created += 1
    return created


def _staff_for(department, role):
    return Staff.objects.filter(department=department, role=role).first()


def seed_users(departments, doctors_by_code, patients):
    """
    Create the documented demo login accounts and link them to their profiles.

    The password comes from ``settings.DEMO_PASSWORD`` (``DEMO_PASSWORD`` in
    ``.env``) and every account is flagged ``is_demo`` so the UI can label it.
    """
    password = settings.DEMO_PASSWORD
    created = 0
    accounts = {}

    for email, username, role, first_name, last_name, designation in DEMO_ACCOUNTS:
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "designation": designation,
                "employee_id": "AST-{}".format(1000 + created),
                "phone": "+91 484 400 1{} (demo)".format(100 + created),
                "is_demo": True,
                "is_active": True,
                "is_staff": role in {RoleCode.SUPER_ADMIN, RoleCode.HOSPITAL_ADMIN},
                "is_superuser": role == RoleCode.SUPER_ADMIN,
            },
        )
        user.set_password(password)
        user.save(update_fields=["password"])
        accounts[username] = user
        created += 1

    # Link accounts to their clinical or staff profiles ---------------------
    links = [
        ("hod", departments["CARD"], doctors_by_code["CARD"][0], None),
        ("doctor", departments["NEUR"], doctors_by_code["NEUR"][1], None),
        ("nurse", departments["GMED"], None, _staff_for(departments["GMED"], Staff.Role.NURSE)),
        ("labtech", departments["PATH"], None, _staff_for(departments["PATH"], Staff.Role.LABORATORY)),
        ("radiologist", departments["RADI"], None, _staff_for(departments["RADI"], Staff.Role.RADIOLOGY)),
        ("pharmacist", departments["GMED"], None, _staff_for(departments["GMED"], Staff.Role.PHARMACIST)),
        ("reception", departments["GMED"], None, _staff_for(departments["GMED"], Staff.Role.RECEPTIONIST)),
        ("billing", departments["GMED"], None, _staff_for(departments["GMED"], Staff.Role.BILLING)),
        ("insurance", departments["GMED"], None, None),
        ("inventory", departments["GMED"], None, _staff_for(departments["GMED"], Staff.Role.ADMINISTRATOR)),
    ]
    for username, department, doctor, staff_member in links:
        user = accounts.get(username)
        if user is None:
            continue
        user.department = department
        user.save(update_fields=["department"])
        if doctor is not None:
            doctor.user = user
            doctor.email = user.email
            doctor.save(update_fields=["user", "email"])
        if staff_member is not None:
            staff_member.user = user
            staff_member.email = user.email
            staff_member.contact = user.phone
            staff_member.save(update_fields=["user", "email", "contact"])

    # The patient portal account is linked to the first demo patient --------
    patient_user = accounts.get("demo.patient")
    if patient_user is not None:
        patient_user.department = departments["CARD"]
        patient_user.save(update_fields=["department"])
        patient = patients[0] if patients else None
        if patient is not None:
            patient.user = patient_user
            patient.name = patient_user.get_full_name()
            patient.email = patient_user.email
            patient.phone = patient_user.phone
            patient.save(update_fields=["user", "name", "email", "phone"])

    return {"accounts": created, "password": password}
