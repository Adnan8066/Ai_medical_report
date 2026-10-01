from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from users.permissions import ModulePermission

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit trail - append only, read by administrators."""

    module = "audit"
    permission_classes = [ModulePermission]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("user").all()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "action", "module", "description", "object_id"]
    ordering_fields = ["created_at", "module", "username"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if module := params.get("module"):
            queryset = queryset.filter(module=module)
        if severity := params.get("severity"):
            queryset = queryset.filter(severity=severity)
        if username := params.get("username"):
            queryset = queryset.filter(username__icontains=username)
        if date_from := params.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to := params.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset
