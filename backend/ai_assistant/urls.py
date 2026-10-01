from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AssistantAskView,
    CapabilitiesView,
    ChatSessionViewSet,
    DocumentAssistantView,
)

router = DefaultRouter()
router.register("sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = router.urls + [
    path("capabilities/", CapabilitiesView.as_view(), name="ai-capabilities"),
    path("ask/", AssistantAskView.as_view(), name="ai-ask"),
    path("documents/ask/", DocumentAssistantView.as_view(), name="ai-document-ask"),
]
