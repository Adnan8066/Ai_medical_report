"""
Friendly, consistent API error payloads.

Raw Django/DRF tracebacks are never returned to normal users.  Every error is
normalised into ``{"detail": ..., "code": ..., "errors": {...}}`` so the React
client can render a single friendly message.
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

FRIENDLY_BY_CODE = {
    "not_found": "The requested record could not be found.",
    "permission_denied": "You do not have permission to perform this action.",
    "authentication_failed": "Your session has expired. Please log in again.",
    "not_authenticated": "Your session has expired. Please log in again.",
    "token_not_valid": "Your session has expired. Please log in again.",
    "throttled": "Too many requests. Please wait a moment and try again.",
    "invalid": "Please check the highlighted fields and try again.",
}


def _flatten(errors, prefix=""):
    """Turn nested serializer errors into a flat {field: message} mapping."""
    flat = {}
    if isinstance(errors, dict):
        for key, value in errors.items():
            flat.update(_flatten(value, prefix=f"{prefix}{key}."))
    elif isinstance(errors, list):
        # A single error on a field is reported against the field itself; only
        # list fields (many=True) get an index so the UI stays readable.
        if len(errors) == 1:
            flat.update(_flatten(errors[0], prefix=prefix))
        else:
            for index, value in enumerate(errors):
                flat.update(_flatten(value, prefix=f"{prefix}{index}."))
    else:
        flat[prefix.rstrip(".") or "detail"] = str(errors)
    return flat


def friendly_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        if isinstance(exc, Http404):
            exc = exceptions.NotFound()
            response = drf_exception_handler(exc, context)
        elif isinstance(exc, DjangoPermissionDenied):
            exc = exceptions.PermissionDenied()
            response = drf_exception_handler(exc, context)
        else:
            # Unexpected server error - log it but never leak internals.
            logger.exception("Unhandled API error in %s", context.get("view"))
            return None

    detail = response.data
    code = getattr(exc, "default_code", "error")

    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
        response.data = {
            "detail": message,
            "code": code,
            "errors": {},
        }
    elif isinstance(detail, dict):
        errors = _flatten(detail)
        response.data = {
            "detail": FRIENDLY_BY_CODE.get(code, "Please check the highlighted fields and try again."),
            "code": code,
            "errors": errors,
        }
    else:
        response.data = {
            "detail": FRIENDLY_BY_CODE.get(code, str(detail)),
            "code": code,
            "errors": {},
        }

    return response
