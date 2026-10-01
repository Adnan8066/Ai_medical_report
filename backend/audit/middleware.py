"""
Request context plus a safety-net audit entry for mutating API calls.

Explicit ``log_action`` calls (which carry object detail) are preferred; the
middleware only fills the gap so that no write ever goes unrecorded.
"""

from . import context
from .services import log_action, module_from_path


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        context.set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            try:
                self._auto_log(request)
            finally:
                context.clear()
        return response

    def _auto_log(self, request):
        if not request.path.startswith("/api/"):
            return
        if request.path.startswith("/api/auth/"):
            return  # handled explicitly by the auth views
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return
        if context.has_explicit_log():
            return
        user = getattr(request, "user", None)
        if not (user and getattr(user, "is_authenticated", False)):
            return
        log_action(
            action=f"{request.method} {request.path}",
            module=module_from_path(request.path),
            description=f"{request.method} request to {request.path}",
            request=request,
        )
