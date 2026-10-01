from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "sources", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "mode", "patient", "updated_at")
    list_filter = ("mode",)
    search_fields = ("title", "user__username")
    inlines = [ChatMessageInline]
