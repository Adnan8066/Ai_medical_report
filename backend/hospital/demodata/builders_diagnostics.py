# Builders for laboratory and radiology activity.

from datetime import date, timedelta

from django.utils import timezone

from laboratory.models import LabReport, LabTest
from laboratory.services import evaluate_flag
from radiology.models import RadiologyReport

from .catalogues import LAB_TESTS


def seed_lab_tests():
    for code, name, category, sample_type, unit, reference, tat, price in LAB_TESTS:
        LabTest.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "category": category,
                "sample_type": sample_type,
                "unit": unit,
                "reference_range": reference,
                "turnaround_hours": tat,
                "price": price,
                "description": "{} - demo test catalogue entry.".format(name),
                "is_active": True,
            },
        )
    return LabTest.objects.count()


def _demo_result(test, rng):
    """Produce a plausible numeric result inside or just outside the range."""
    from laboratory.services import parse_range

    bounds = parse_range(test.reference_range)
    if bounds is None:
        return None, rng.choice(["Negative", "Not detected", "Within normal limits"])
    low, high = bounds
    span = float(high) - float(low) or 1.0
    drift = rng.choice([0, 0, 0, 1, -1, 2])
    value = round(float(low) + span * rng.uniform(0.15, 0.9) + drift * span * 0.25, 2)
    return value, str(value)


def seed_lab_reports(patients, rng):
    """Create ordered, in-progress and completed laboratory reports."""
    created = 0
    counter = 1001
    tests = list(LabTest.objects.all())
    technicians = ["Fathima Rasheed", "Suresh Kumar", "Geethu Chandran", "Anand Varghese"]
    if not tests:
        return 0

    for patient in patients:
        orders = rng.randint(1, 3) if patient.admission_status == "admitted" else rng.randint(1, 2)
        for _ in range(orders):
            test = rng.choice(tests)
            ordered_at = timezone.now() - timedelta(
                days=rng.randint(0, 20), hours=rng.randint(0, 23)
            )
            status = rng.choices(
                [
                    LabReport.Status.ORDERED,
                    LabReport.Status.SAMPLE_COLLECTED,
                    LabReport.Status.PROCESSING,
                    LabReport.Status.COMPLETED,
                ],
                weights=[18, 14, 12, 56],
                k=1,
            )[0]
            numeric, result_text = _demo_result(test, rng)
            completed = status == LabReport.Status.COMPLETED
            LabReport.objects.update_or_create(
                lab_id="LAB-{}".format(counter),
                defaults={
                    "patient": patient,
                    "doctor": patient.assigned_doctor,
                    "test": test,
                    "ordered_at": ordered_at,
                    "sample_collected_at": ordered_at + timedelta(hours=1)
                    if status != LabReport.Status.ORDERED
                    else None,
                    "report_date": ordered_at + timedelta(hours=rng.randint(4, 30))
                    if completed
                    else None,
                    "result": result_text if completed else "",
                    "numeric_value": numeric if completed else None,
                    "unit": test.unit,
                    "reference_range": test.reference_range,
                    "flag": evaluate_flag(numeric, test.reference_range)
                    if completed
                    else LabReport.Flag.UNKNOWN,
                    "status": status,
                    "technician_name": rng.choice(technicians),
                    "remarks": "Demo result. Reference range shown for guidance only.",
                    "price": test.price,
                },
            )
            counter += 1
            created += 1
    return created


SCAN_CATALOGUE = [
    ("xray", "Chest PA", 600, "No focal consolidation. Cardiac silhouette within normal limits."),
    ("xray", "Right Knee AP/Lateral", 700, "Mild joint space narrowing noted. No fracture."),
    ("xray", "Lumbar Spine AP/Lateral", 750, "Straightening of lumbar lordosis. No acute bony injury."),
    ("ct", "CT Brain Plain", 4500, "No acute intracranial haemorrhage or infarct in this demo study."),
    ("ct", "CT Abdomen and Pelvis", 6800, "No free fluid or collection visualised in this demo study."),
    ("mri", "MRI Brain with Contrast", 9500, "No evidence of acute demyelination in this demo study."),
    ("mri", "MRI Lumbar Spine", 8800, "L4-L5 disc bulge with mild impression in this demo study."),
    ("ultrasound", "Ultrasound Abdomen", 1800, "Liver, spleen and kidneys appear normal in this demo study."),
    ("ultrasound", "Obstetric Ultrasound", 2200, "Single live intrauterine gestation. Demo study."),
    ("ecg", "12 Lead ECG", 400, "Sinus rhythm. No acute ST-T changes in this demo tracing."),
    ("echo", "Echocardiography", 2800, "Normal left ventricular systolic function in this demo study."),
]


def seed_radiology(patients, rng):
    """Create imaging requests and reported studies."""
    created = 0
    counter = 1001
    radiologists = ["Sandeep Kurup", "Precision Imaging Team", "Divya Nair"]

    for patient in patients:
        studies = 2 if patient.patient_type in {"inpatient", "icu", "emergency"} else 1
        for _ in range(studies):
            scan_type, body_part, price, findings = rng.choice(SCAN_CATALOGUE)
            appointment = timezone.now() - timedelta(
                days=rng.randint(0, 25), hours=rng.randint(0, 20)
            )
            status = rng.choices(
                [
                    RadiologyReport.Status.ORDERED,
                    RadiologyReport.Status.SCHEDULED,
                    RadiologyReport.Status.IN_PROGRESS,
                    RadiologyReport.Status.COMPLETED,
                ],
                weights=[20, 18, 12, 50],
                k=1,
            )[0]
            completed = status == RadiologyReport.Status.COMPLETED
            RadiologyReport.objects.update_or_create(
                scan_id="RAD-{}".format(counter),
                defaults={
                    "patient": patient,
                    "doctor": patient.assigned_doctor,
                    "scan_type": scan_type,
                    "body_part": body_part,
                    "appointment_date": appointment,
                    "radiologist_name": rng.choice(radiologists),
                    "technician_name": "Demo Radiography Team",
                    "status": status,
                    "findings": findings if completed else "",
                    "impression": (
                        "Demo impression recorded for the AsterNova showcase."
                        if completed
                        else ""
                    ),
                    "report": (
                        "Technical details: standard protocol acquisition. "
                        + findings
                        if completed
                        else ""
                    ),
                    "report_date": appointment + timedelta(hours=rng.randint(2, 36))
                    if completed
                    else None,
                    "price": price,
                },
            )
            counter += 1
            created += 1
    return created


def lab_summary():
    return {
        "tests": LabTest.objects.count(),
        "reports": LabReport.objects.count(),
        "radiology": RadiologyReport.objects.count(),
        "as_of": date.today(),
    }
