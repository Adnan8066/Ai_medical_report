# Builders for the demo hospital's core records (hospital, roles, departments,
# clinicians and the wider workforce).

from datetime import date, timedelta

from doctors.models import Doctor
from hospital.models import Department, Hospital
from staff.models import Shift, Staff
from users.models import Role, RoleCode
from users.roles import DEFAULT_ROLE_PERMISSIONS, MODULE_LABELS

from .catalogues import DEPARTMENTS, SHIFTS
from .names import FEMALE_FIRST_NAMES, MALE_FIRST_NAMES, SURNAMES

HOSPITAL = {
    "name": "AsterNova Multispeciality Hospital",
    "code": "ASTERNOVA",
    "hospital_type": "Multispeciality Hospital",
    "established_year": 2012,
    "address_line1": "Plot 42, AsterNova Health Campus",
    "address_line2": "Seaport-Airport Road, Kakkanad",
    "city": "Kochi",
    "state": "Kerala",
    "postal_code": "682030",
    "country": "India",
    "phone": "+91 484 400 1234 (demo)",
    "emergency_number": "+91 484 400 1088 (demo)",
    "email": "care@asternova.demo",
    "website": "https://www.asternova.demo (fictional)",
    "registration_number": "KL/DEMO/HOSP/2012/0042",
    "total_beds": 350,
    "icu_beds": 40,
    "emergency_beds": 20,
    "about": (
        "AsterNova Multispeciality Hospital is a fictional 350 bed multispeciality "
        "hospital created for this demonstration platform. Every patient, clinician, "
        "record and contact detail shown in the application is fabricated demo data."
    ),
}

DEMO_ACCOUNTS = [
    ("superadmin@asternova.demo", "superadmin", RoleCode.SUPER_ADMIN, "Ananya", "Menon", "Hospital Leadership"),
    ("admin@asternova.demo", "hospitaladmin", RoleCode.HOSPITAL_ADMIN, "Rohit", "Varma", "Hospital Administration"),
    ("hod@asternova.demo", "hod", RoleCode.HOD, "Arjun", "Menon", "Cardiology"),
    ("doctor@asternova.demo", "doctor", RoleCode.DOCTOR, "Meera", "Nair", "Neurology"),
    ("nurse@asternova.demo", "nurse", RoleCode.NURSE, "Sreelakshmi", "Pillai", "General Medicine"),
    ("reception@asternova.demo", "reception", RoleCode.RECEPTIONIST, "Ann", "Thomas", "Front Office"),
    ("lab@asternova.demo", "labtech", RoleCode.LAB_TECHNICIAN, "Fathima", "Rasheed", "Pathology"),
    ("radiologist@asternova.demo", "radiologist", RoleCode.RADIOLOGIST, "Sandeep", "Kurup", "Radiology"),
    ("pharmacist@asternova.demo", "pharmacist", RoleCode.PHARMACIST, "Vinod", "Pillai", "Pharmacy"),
    ("billing@asternova.demo", "billing", RoleCode.BILLING_STAFF, "Dinesh", "Kumar", "Finance"),
    ("insurance@asternova.demo", "insurance", RoleCode.INSURANCE_STAFF, "Remya", "Suresh", "Insurance Desk"),
    ("inventory@asternova.demo", "inventory", RoleCode.INVENTORY_MANAGER, "Manju", "Raghunath", "Central Stores"),
    ("patient@asternova.demo", "demo.patient", RoleCode.PATIENT, "Rahul", "Krishnan", "Patient Portal"),
]


def seed_roles():
    """Create the configurable role records with their default matrices."""
    count = 0
    for code, label in RoleCode.choices:
        Role.objects.update_or_create(
            code=code,
            defaults={
                "name": label,
                "is_system": True,
                "description": "{} access to the AsterNova platform.".format(label),
                "permissions": DEFAULT_ROLE_PERMISSIONS.get(code, {}),
            },
        )
        count += 1
    return {"roles": count, "modules": len(MODULE_LABELS)}


def seed_hospital():
    hospital, _ = Hospital.objects.update_or_create(
        code=HOSPITAL["code"], defaults=HOSPITAL
    )
    return hospital


def seed_shifts():
    for shift in SHIFTS:
        Shift.objects.update_or_create(
            code=shift["code"],
            defaults={
                "name": shift["name"],
                "start_time": shift["start_time"],
                "end_time": shift["end_time"],
                "description": shift["description"],
                "is_emergency_shift": shift["is_emergency_shift"],
                "color": shift["color"],
            },
        )
    return Shift.objects.count()


def seed_departments():
    departments = {}
    for entry in DEPARTMENTS:
        department, _ = Department.objects.update_or_create(
            code=entry["code"],
            defaults={
                "name": entry["name"],
                "floor": entry["floor"],
                "location": entry["location"],
                "contact_extension": entry["extension"],
                "phone": "+91 484 400 {} (demo)".format(entry["extension"]),
                "email": "{}@asternova.demo".format(entry["code"].lower()),
                "bed_count": entry["beds"],
                "description": entry["description"],
                "is_clinical": entry["is_clinical"],
                "is_active": True,
            },
        )
        departments[entry["code"]] = department
    return departments


def unique_doctor_name(rng, used):
    for _ in range(300):
        pool = MALE_FIRST_NAMES if rng.random() < 0.6 else FEMALE_FIRST_NAMES
        name = "Dr. {} {}".format(rng.choice(pool), rng.choice(SURNAMES))
        if name not in used:
            used.add(name)
            return name
    fallback = "Dr. Demo {}".format(len(used) + 1)
    used.add(fallback)
    return fallback


def seed_doctors(departments, rng):
    """
    Create one HOD plus two consultants for every department.

    HOD names, qualifications and room numbers come from the department
    catalogue; the remaining clinicians are generated from the fictional name
    pools so the roster looks full and realistic.
    """
    used_names = set()
    doctors_by_code = {}
    counter = 1001
    today = date.today()

    for entry in DEPARTMENTS:
        department = departments[entry["code"]]
        hod = entry["hod"]
        used_names.add(hod["name"])
        doctor, _ = Doctor.objects.update_or_create(
            doctor_id="DOC-{}".format(counter),
            defaults={
                "name": hod["name"],
                "gender": "female" if hod["name"].split()[-2] in FEMALE_FIRST_NAMES else "male",
                "department": department,
                "designation": Doctor.Designation.HOD,
                "is_hod": True,
                "qualification": hod["qualification"],
                "experience_years": hod["experience"],
                "specialization": hod["specialization"],
                "consultation_fee": 900,
                "room_number": hod["room"],
                "phone_extension": entry["extension"],
                "phone": "+91 484 400 {} (demo)".format(entry["extension"]),
                "email": "{}.hod@asternova.demo".format(entry["code"].lower()),
                "availability": Doctor.Availability.AVAILABLE,
                "available_days": "Mon, Wed, Fri",
                "opd_schedule": {
                    "mon": ["09:00-13:00"],
                    "wed": ["09:00-13:00", "15:00-17:00"],
                    "fri": ["09:00-13:00"],
                },
                "joining_date": today - timedelta(days=365 * hod["experience"]),
                "languages": "English, Malayalam, Hindi",
                "status": Doctor.Status.ACTIVE,
            },
        )
        counter += 1
        doctors_by_code.setdefault(entry["code"], []).append(doctor)

    for entry in DEPARTMENTS:
        department = departments[entry["code"]]
        for index in range(2):
            name = unique_doctor_name(rng, used_names)
            doctor_id = "DOC-{}".format(counter)
            counter += 1
            extra, _ = Doctor.objects.update_or_create(
                doctor_id=doctor_id,
                defaults={
                    "name": name,
                    "gender": "female" if name.split()[-2] in FEMALE_FIRST_NAMES else "male",
                    "department": department,
                    "designation": (
                        Doctor.Designation.SENIOR_CONSULTANT
                        if index == 0
                        else Doctor.Designation.CONSULTANT
                    ),
                    "is_hod": False,
                    "qualification": "MBBS, {} ({})".format(
                        rng.choice(["MD", "MS", "DNB"]), entry["name"]
                    ),
                    "experience_years": rng.randint(4, 14),
                    "specialization": "General {}".format(entry["name"]),
                    "consultation_fee": rng.choice([500, 600, 700, 800]),
                    "room_number": "{}-{}".format(entry["code"][:2], 120 + counter % 80),
                    "phone_extension": str(int(entry["extension"]) + index + 1),
                    "phone": "+91 484 400 2{} (demo)".format(rng.randint(100, 999)),
                    "email": "{}.{}.@asternova.demo".format(
                        entry["code"].lower(), doctor_id.lower()
                    ),
                    "availability": rng.choice(
                        [
                            Doctor.Availability.AVAILABLE,
                            Doctor.Availability.IN_CONSULTATION,
                            Doctor.Availability.ON_ROUNDS,
                            Doctor.Availability.IN_SURGERY,
                        ]
                    ),
                    "available_days": rng.choice(
                        ["Mon, Tue, Thu", "Tue, Thu, Sat", "Mon, Wed, Fri", "Daily OPD"]
                    ),
                    "opd_schedule": {"mon": ["10:00-14:00"], "thu": ["10:00-14:00"]},
                    "joining_date": today - timedelta(days=365 * rng.randint(2, 12)),
                    "languages": "English, Malayalam",
                    "status": Doctor.Status.ACTIVE,
                },
            )
            doctors_by_code[entry["code"]].append(extra)

    for entry in DEPARTMENTS:
        department = departments[entry["code"]]
        department.hod = doctors_by_code[entry["code"]][0]
        department.save(update_fields=["hod"])
    return doctors_by_code
