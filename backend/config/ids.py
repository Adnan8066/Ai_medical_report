"""Human readable sequential identifiers (APT-1001, LAB-1001, ...)."""

from django.db import transaction


def next_sequential_id(model, field, prefix, start=1001, width=4):
    """
    Return the next free ``<PREFIX>-<number>`` identifier for ``model.field``.

    Wrapped in a transaction with ``select_for_update`` so concurrent inserts
    cannot collide.
    """
    lookup = {f"{field}__startswith": f"{prefix}-"}
    with transaction.atomic():
        last = (
            model.objects.select_for_update()
            .filter(**lookup)
            .order_by(f"-{field}")
            .values_list(field, flat=True)
            .first()
        )
    if not last:
        number = start
    else:
        try:
            number = int(last.rsplit("-", 1)[1]) + 1
        except (IndexError, ValueError):
            number = start
    return f"{prefix}-{str(number).zfill(width)}" if width else f"{prefix}-{number}"
