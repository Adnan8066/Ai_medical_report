# Builders for the day-to-day clinical flow: appointments, OPD, emergency,
# admissions, nursing assignments and discharge summaries.

from datetime import date, time, timedelta

from django.utils import timezone

from admissions.models import Admission, DischargeSummary
from appointments.models import Appointment
from beds.models import Bed
from emergency.models import EmergencyVisit
from opd.models import OPDVisit
from patients.models import NurseAssignment
from staff.models import Staff

from .names import COMPLAINTS, DEFAULT_COMPLAINTS, EMERGENCY_COMPLAINTS

SLOTS = [time(hour, minute) for hour in range(9, 18) for minute in (0, 30)]


def seed_appointments(patients, doctors_by_code, rng):
    """Create a realistic booking diary spanning the last month and next two weeks."""
    created = 0
    counter = 1001
    today = date.today()

    for patient in patients:
        bookings = 1 if patient.patient_type in {"inpatient", "icu"} else 2
        for _ in range(bookings):
            department_code = patient.department.code if patient.department else ""
            doctors = doctors_by_code.get(department_code, [])
            doctor = rng.choice(doctors) if doctors else None
            if doctor is None:
                continue

            offset = rng.randint(-30, 14)
            appointment_date = today + timedelta(days=offset)
            if offset < 0:
                status = rng.choices(
                    ["completed", "cancelled", "no_show"],
                    weights=[85, 8, 7],
                    k=1,
                )[0]
            elif offset == 0:
                status = rng.choice(["confirmed", "in_consultation", "completed"])
            else:
                status = rng.choice(["scheduled", "confirmed", "confirmed"])

            complaints = COMPLAINTS.get(
                patient.department.name if patient.department else "", DEFAULT_COMPLAINTS
            )
            Appointment.objects.update_or_create(
                appointment_id="APT-{}".format(counter),
                defaults={
                    "patient": patient,
                    "doctor": doctor,
                    "department": patient.department,
                    "date": appointment_date,
                    "time": rng.choice(SLOTS),
                    "appointment_type": rng.choice(
                        [
                            Appointment.AppointmentType.CONSULTATION,
                            Appointment.AppointmentType.FOLLOW_UP,
                            Appointment.AppointmentType.PROCEDURE,
                            Appointment.AppointmentType.DIAGNOSTIC,
                        ]
                    ),
                    "reason": rng.choice(complaints),
                    "notes": "Fictional demo appointment.",
                    "token_number": rng.randint(1, 60),
                    "status": status,
                    "reminder_sent": rng.random() < 0.6,
                },
            )
            counter += 1
            created += 1
    return created


def seed_emergency(departments, doctors_by_code, patients, rng):
    """Create emergency cases across today and the previous three days."""
    created = 0
    counter = 1001
    now = timezone.now()
    emergency_patients = [
        patient
        for patient in patients
        if patient.patient_type in {"emergency", "icu", "inpatient"}
    ]
    rng.shuffle(emergency_patients)
    doctors = doctors_by_code.get("EMER", [])
    nurses = list(
        Staff.objects.filter(department=departments["EMER"], role=Staff.Role.NURSE)
    )
    beds = list(Bed.objects.filter(category="emergency")[:20])

    for index, patient in enumerate(emergency_patients[:40]):
        day_offset = 0 if index < 20 else rng.randint(1, 3)
        arrival = now - timedelta(
            days=day_offset, hours=rng.randint(0, 10), minutes=rng.randint(0, 59)
        )
        priority = rng.choices(
            ["critical", "high", "medium", "low"], weights=[15, 30, 35, 20], k=1
        )[0]
        status = rng.choice(
            [
                EmergencyVisit.Status.TRIAGED,
                EmergencyVisit.Status.IN_TREATMENT,
                EmergencyVisit.Status.OBSERVATION,
                EmergencyVisit.Status.ADMITTED,
                EmergencyVisit.Status.DISCHARGED,
            ]
        )
        closed = arrival + timedelta(minutes=rng.randint(60, 480)) if day_offset else None
        EmergencyVisit.objects.update_or_create(
            case_id="ER-{}".format(counter),
            defaults={
                "patient": patient,
                "arrival_time": arrival,
                "triage_time": arrival + timedelta(minutes=rng.randint(2, 20)),
                "priority": priority,
                "assigned_doctor": rng.choice(doctors) if doctors else patient.assigned_doctor,
                "assigned_nurse": rng.choice(nurses) if nurses else None,
                "bed": rng.choice(beds) if priority in {"critical", "high"} and beds else None,
                "chief_complaint": rng.choice(EMERGENCY_COMPLAINTS),
                "condition_notes": (
                    "Demo emergency record. Patient assessed by the emergency team; "
                    "observations and disposition recorded for demonstration only."
                ),
                "vitals_summary": "BP {}/{}, pulse {}, SpO2 {}%".format(
                    rng.randint(96, 168),
                    rng.randint(60, 100),
                    rng.randint(58, 126),
                    rng.randint(88, 100),
                ),
                "treatment_given": "Initial stabilisation and monitoring in the emergency bay.",
                "disposition": rng.choice(
                    ["Admitted to ward", "Observed in ED", "Discharged with advice"]
                ),
                "status": status,
                "closed_at": closed,
            },
        )
        counter += 1
        created += 1
    return created


def seed_discharge_summaries(patients, rng):
    """Create discharge documentation in various workflow states."""
    created = 0
    counter = 1001
    candidates = [
        patient
        for patient in patients
        if patient.patient_type in {"discharged", "inpatient"}
    ]
    rng.shuffle(candidates)

    # Summaries are keyed on the admission, so rebuild the seeded ones to keep
    # the identifier scheme consistent across repeat runs.
    DischargeSummary.objects.filter(admission__isnull=False).delete()

    for patient in candidates[:90]:
        admission = Admission.objects.filter(patient=patient).first()
        if admission is None:
            continue
        if admission.status == Admission.Status.DISCHARGED:
            status = DischargeSummary.Status.COMPLETED
            doctor_approved = True
            complete = True
        else:
            status = rng.choice(
                [
                    DischargeSummary.Status.DRAFT,
                    DischargeSummary.Status.PENDING_APPROVAL,
                    DischargeSummary.Status.APPROVED,
                ]
            )
            doctor_approved = status != DischargeSummary.Status.DRAFT
            complete = False

        discharge_date = admission.discharge_date or (
            timezone.now() + timedelta(days=rng.randint(1, 4))
        )
        # One summary per admission (a OneToOne relation), keyed on the
        # admission so repeat runs stay idempotent.
        DischargeSummary.objects.update_or_create(
            admission=admission,
            defaults={
                "discharge_id": "DS-{}".format(admission.admission_id.split("-")[-1]),
                "patient": patient,
                "doctor": patient.assigned_doctor,
                "admission_date": admission.admission_date,
                "discharge_date": discharge_date,
                "diagnosis_summary": (
                    "Demo discharge summary. The patient was admitted with the presenting "
                    "complaint, investigated and managed as per the treating team's plan."
                ),
                "procedures": rng.choice(
                    ["None", "Diagnostic endoscopy", "Minor surgical procedure", "Physiotherapy"]
                ),
                "medications": (
                    "Tab. Paracetamol 500 mg SOS; Tab. Pantoprazole 40 mg once daily "
                    "(demo medication list)."
                ),
                "follow_up_instructions": (
                    "Review in the outpatient department in one week. Report earlier if "
                    "symptoms worsen. Continue prescribed medication."
                ),
                "follow_up_date": (discharge_date + timedelta(days=7)).date()
                if discharge_date
                else None,
                "condition_on_discharge": rng.choice(
                    ["Stable and ambulatory", "Improved", "Afebrile and comfortable"]
                ),
                "status": status,
                "doctor_approved": doctor_approved,
                "final_bill_settled": complete,
                "pharmacy_cleared": complete or rng.random() < 0.5,
                "insurance_processed": complete or rng.random() < 0.4,
                "follow_up_scheduled": complete or rng.random() < 0.6,
            },
        )
        counter += 1
        created += 1
    return created


def seed_admissions(patients, rng):
    """
    Create inpatient stays.

    Currently admitted patients get an open admission linked to the bed they
    occupy; discharged patients get a completed historical stay.
    """
    created = 0
    counter = 1001
    now = timezone.now()
    bed_by_patient = {
        bed.patient_id: bed for bed in Bed.objects.exclude(patient=None).select_related("ward")
    }

    for patient in patients:
        if patient.admission_status == "admitted":
            bed = bed_by_patient.get(patient.pk)
            admission_date = now - timedelta(
                days=rng.randint(1, 14), hours=rng.randint(0, 20)
            )
            status = rng.choice(
                [
                    Admission.Status.ADMITTED,
                    Admission.Status.UNDER_TREATMENT,
                    Admission.Status.UNDER_TREATMENT,
                    Admission.Status.READY_FOR_DISCHARGE,
                ]
            )
            discharge_date = None
        elif patient.patient_type == "discharged":
            bed = None
            admission_date = now - timedelta(days=rng.randint(12, 40))
            discharge_date = admission_date + timedelta(days=rng.randint(3, 11))
            status = Admission.Status.DISCHARGED
        else:
            continue

        Admission.objects.update_or_create(
            admission_id="ADM-{}".format(counter),
            defaults={
                "patient": patient,
                "doctor": patient.assigned_doctor,
                "attending_doctor": patient.assigned_doctor,
                "department": patient.department,
                "admission_date": admission_date,
                "expected_discharge_date": (admission_date + timedelta(days=rng.randint(3, 9))).date(),
                "discharge_date": discharge_date,
                "ward": bed.ward if bed else None,
                "bed": bed,
                "bed_number": bed.bed_number if bed else "",
                "nurse": rng.choice(
                    list(
                        Staff.objects.filter(
                            department=patient.department, role=Staff.Role.NURSE
                        )
                    )
                    or [None]
                ),
                "admission_reason": rng.choice(
                    [
                        "Evaluation and management of presenting complaint",
                        "Elective procedure under general surgery",
                        "Observation for uncontrolled symptoms",
                        "Post-operative monitoring and recovery",
                    ]
                ),
                "diagnosis": "Provisional inpatient diagnosis recorded for demo purposes.",
                "treatment_plan": (
                    "Demo treatment plan: intravenous fluids, symptomatic management, "
                    "daily review and investigation follow-up."
                ),
                "status": status,
                "notes": "Fictional inpatient stay created for the AsterNova showcase.",
            },
        )
        counter += 1
        created += 1
    return created


def seed_nurse_assignments(patients, departments, rng):
    """Assign nurses to every current inpatient."""
    created = 0
    for patient in patients:
        if patient.admission_status != "admitted":
            continue
        nurses = list(
            Staff.objects.filter(department=patient.department, role=Staff.Role.NURSE)
        )
        if not nurses:
            continue
        nurse = rng.choice(nurses)
        NurseAssignment.objects.update_or_create(
            patient=patient,
            nurse=nurse,
            assigned_on=date.today(),
            defaults={
                "shift": nurse.shift,
                "status": NurseAssignment.Status.ACTIVE,
                "notes": "Primary nurse for the current demo shift.",
            },
        )
        created += 1
    return created


def seed_opd_visits(patients, rng):
    """Create consultation records for patients who attended the OPD."""
    created = 0
    counter = 1001
    today = date.today()

    for patient in patients:
        visits = 2 if patient.patient_type in {"opd", "follow_up", "discharged"} else 1
        doctor = patient.assigned_doctor
        if doctor is None:
            continue
        for _ in range(visits):
            visit_date = today - timedelta(days=rng.randint(0, 45))
            complaints = COMPLAINTS.get(
                patient.department.name if patient.department else "", DEFAULT_COMPLAINTS
            )
            chief = rng.choice(complaints)
            OPDVisit.objects.update_or_create(
                visit_id="OPD-{}".format(counter),
                defaults={
                    "patient": patient,
                    "doctor": doctor,
                    "department": patient.department,
                    "visit_date": visit_date,
                    "visit_time": rng.choice(SLOTS),
                    "chief_complaint": chief,
                    "symptoms": "Reported {} with no acute distress.".format(chief.lower()),
                    "consultation_notes": (
                        "Demo consultation note. Vitals reviewed and systemic examination "
                        "recorded as unremarkable. Investigations advised for demonstration."
                    ),
                    "diagnosis": "Provisional impression recorded for demonstration.",
                    "prescription_notes": "See the linked demo prescription for medicines.",
                    "advice": "Diet counselling, medication compliance and review as scheduled.",
                    "follow_up_date": visit_date + timedelta(days=rng.choice([7, 14, 30])),
                    "consultation_fee": doctor.consultation_fee,
                    "status": rng.choice(
                        [
                            OPDVisit.Status.COMPLETED,
                            OPDVisit.Status.COMPLETED,
                            OPDVisit.Status.FOLLOW_UP_REQUIRED,
                            OPDVisit.Status.WAITING,
                        ]
                    ),
                },
            )
            counter += 1
            created += 1
    return created
