"""Per-request context so services can reach the active request/thread."""

import threading

_state = threading.local()


def set_current_request(request):
    _state.request = request
    _state.explicit_log = False


def get_current_request():
    return getattr(_state, "request", None)


def mark_explicit_log():
    _state.explicit_log = True


def has_explicit_log():
    return getattr(_state, "explicit_log", False)


def clear():
    _state.request = None
    _state.explicit_log = False


def client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
