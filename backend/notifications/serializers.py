from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    level_label = serializers.CharField(source="get_level_display", read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    recipient_name = serializers.CharField(
        source="recipient.full_name", read_only=True, default=None
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_name",
            "role_target",
            "title",
            "message",
            "category",
            "category_label",
            "level",
            "level_label",
            "is_read",
            "read_at",
            "link",
            "created_at",
            "expires_at",
        ]
        read_only_fields = ["created_at", "read_at"]
