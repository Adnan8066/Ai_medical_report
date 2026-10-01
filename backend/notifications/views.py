from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(BaseViewSet):
    module = "notifications"
    queryset = Notification.objects.select_related("recipient").all()
    serializer_class = NotificationSerializer
    search_fields = ["title", "message"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if not (user.is_superuser or user.is_administrator):
            queryset = queryset.filter(
                Q(recipient=user) | Q(recipient__isnull=True, role_target__in=["", user.role])
            )
        params = self.request.query_params
        if params.get("unread") == "true":
            queryset = queryset.filter(is_read=False)
        if category := params.get("category"):
            queryset = queryset.filter(category=category)
        if level := params.get("level"):
            queryset = queryset.filter(level=level)
        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.get_queryset()
        unread = queryset.filter(is_read=False)
        return Response(
            {
                "total": queryset.count(),
                "unread": unread.count(),
                "critical": unread.filter(level=Notification.Level.CRITICAL).count(),
                "recent": NotificationSerializer(unread[:8], many=True).data,
            }
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({"detail": f"{updated} notification(s) marked as read."})
