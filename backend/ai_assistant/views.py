from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from documents.models import MedicalDocument
from documents.services import ai as document_ai
from documents.services import rag
from users.permissions import ModulePermission

from .engine import SUGGESTED_QUESTIONS, answer_question
from .models import ChatMessage, ChatSession
from .serializers import (
    AskSerializer,
    ChatSessionDetailSerializer,
    ChatSessionSerializer,
    DocumentAskSerializer,
)


class CapabilitiesView(APIView):
    """What the assistant can and cannot do - shown in the UI."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "suggestions": SUGGESTED_QUESTIONS,
                "provider": document_ai.answer_status(),
                "can": [
                    "Retrieve operational records you are authorised to view.",
                    "Summarise and organise uploaded documents.",
                    "Quote the exact document text that supports an answer.",
                ],
                "cannot": [
                    "Diagnose a condition.",
                    "Prescribe or recommend medicines.",
                    "Recommend treatment or triage decisions.",
                    "Replace review by an authorised healthcare professional.",
                ],
                "disclaimer": document_ai.AI_DISCLAIMER,
            }
        )


class AssistantAskView(APIView):
    """Hospital assistant: answers from authorised operational data."""

    permission_classes = [ModulePermission]
    module = "ai"
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        result = answer_question(question, request.user)

        session = self._session(request, serializer.validated_data.get("session"), question)
        ChatMessage.objects.create(session=session, role=ChatMessage.Role.USER, content=question)
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=result["answer"],
            sources=result.get("sources", []),
            data_snapshot=result.get("data", {}),
        )

        return Response(
            {
                "session": ChatSessionSerializer(session).data,
                "answer": result["answer"],
                "intent": result["intent"],
                "data": result.get("data", {}),
                "sources": result.get("sources", []),
                "suggestions": result.get("suggestions", []),
                "disclaimer": result["disclaimer"],
            }
        )

    @staticmethod
    def _session(request, session_id, question):
        if session_id:
            session = ChatSession.objects.filter(
                pk=session_id, user=request.user, mode=ChatSession.Mode.HOSPITAL
            ).first()
            if session is not None:
                return session
        return ChatSession.objects.create(
            user=request.user,
            mode=ChatSession.Mode.HOSPITAL,
            title=question[:80],
            provider="demo",
        )


class DocumentAssistantView(APIView):
    """
    Document assistant (RAG): answers only from documents the caller may see,
    always with source references and never with invented content.
    """

    permission_classes = [ModulePermission]
    module = "ai"
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        serializer = DocumentAskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        patient_id = serializer.validated_data.get("patient")

        documents = MedicalDocument.objects.all()
        patient = None
        if patient_id:
            patient = getattr(request.user, "patient_profile", None)
            if patient is None or patient.pk != patient_id:
                from patients.models import Patient

                patient = Patient.objects.filter(pk=patient_id).first()
            # Object level scoping through the documents permission layer.
            from users.scoping import PatientScopedQuerysetMixin

            class _Scoped(PatientScopedQuerysetMixin):
                request = None
                patient_lookup = "patient"

            scoper = _Scoped()
            scoper.request = request
            documents = scoper.scope_queryset(documents.filter(patient_id=patient_id))

        results = rag.search(question, documents)
        answer, sources = rag.build_answer(
            question, results, patient_name=patient.name if patient else ""
        )

        session = self._session(request, serializer.validated_data.get("session"), question, patient)
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=question
        )
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=answer,
            sources=sources,
        )

        return Response(
            {
                "session": ChatSessionSerializer(session).data,
                "answer": answer,
                "results": results,
                "sources": sources,
                "patient": patient.name if patient else None,
                "disclaimer": document_ai.AI_DISCLAIMER,
                "grounding": (
                    "This answer is composed only from the retrieved document text. "
                    "No information has been invented."
                ),
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _session(request, session_id, question, patient):
        if session_id:
            session = ChatSession.objects.filter(
                pk=session_id, user=request.user, mode=ChatSession.Mode.DOCUMENT
            ).first()
            if session is not None:
                return session
        return ChatSession.objects.create(
            user=request.user,
            mode=ChatSession.Mode.DOCUMENT,
            title=question[:80],
            patient=patient,
            provider="demo",
        )


class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Conversation history for the signed-in user."""

    module = "ai"
    permission_classes = [ModulePermission]
    queryset = ChatSession.objects.all()

    def get_queryset(self):
        queryset = ChatSession.objects.filter(user=self.request.user).prefetch_related(
            "messages"
        )
        if mode := self.request.query_params.get("mode"):
            queryset = queryset.filter(mode=mode)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChatSessionDetailSerializer
        return ChatSessionSerializer
