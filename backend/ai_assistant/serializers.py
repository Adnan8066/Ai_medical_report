from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "role",
            "content",
            "sources",
            "data_snapshot",
            "provider",
            "created_at",
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source="messages.count", read_only=True)
    patient_name = serializers.CharField(
        source="patient.name", read_only=True, default=None
    )

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "mode",
            "title",
            "patient",
            "patient_name",
            "provider",
            "message_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "provider"]


class ChatSessionDetailSerializer(ChatSessionSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta(ChatSessionSerializer.Meta):
        fields = ChatSessionSerializer.Meta.fields + ["messages"]


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    session = serializers.IntegerField(required=False, allow_null=True)


class DocumentAskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    patient = serializers.IntegerField(required=False, allow_null=True)
    session = serializers.IntegerField(required=False, allow_null=True)
