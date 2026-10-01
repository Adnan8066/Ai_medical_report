"""Patient-domain helpers."""

from django.db import transaction

from .models import Patient


def next_patient_id():
    """Generate the next sequential demo patient identifier (PAT-10001...)."""
    with transaction.atomic():
        last = (
            Patient.objects.select_for_update()
            .filter(patient_id__startswith="PAT-")
            .order_by("-patient_id")
            .values_list("patient_id", flat=True)
            .first()
        )
        if not last:
            return "PAT-10001"
        try:
            number = int(last.split("-")[1])
        except (IndexError, ValueError):
            number = 10000
        return f"PAT-{number + 1}"
