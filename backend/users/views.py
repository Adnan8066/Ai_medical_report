from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from audit.services import log_action
from config.viewsets import BaseViewSet

from .models import Role, RoleCode, User
from .permissions import IsAdministrator, ModulePermission
from .roles import MODULE_LABELS
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    MeSerializer,
    RoleSerializer,
    UserSerializer,
    UserWriteSerializer,
)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["name"] = user.full_name
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class LoginView(APIView):
    """Authenticate with email/username + password and return JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier)
        ).first()

        if user is None:
            log_action(
                "Failed login",
                "users",
                description=f"Failed login attempt for unknown identifier '{identifier}'.",
                severity="warning",
                request=request,
            )
            return Response(
                {
                    "detail": "Invalid email/username or password.",
                    "code": "authentication_failed",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        authenticated = authenticate(request, username=user.username, password=password)
        if authenticated is None or not authenticated.is_active:
            log_action(
                "Failed login",
                "users",
                user=user,
                description=f"Failed login attempt for {user.username}.",
                severity="warning",
                request=request,
            )
            return Response(
                {
                    "detail": "Invalid email/username or password.",
                    "code": "authentication_failed",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.last_login = timezone.now()
        user.last_seen = user.last_login
        user.save(update_fields=["last_login", "last_seen"])

        log_action(
            "Signed in",
            "users",
            user=user,
            description=f"{user.full_name} signed in as {user.get_role_display()}.",
            request=request,
        )

        return Response(
            {
                "user": MeSerializer(user).data,
                "tokens": _tokens_for(user),
                "demo_mode": settings.DEMO_MODE,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Blacklist the supplied refresh token and end the session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("refresh")
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                pass
        log_action("Signed out", "users", description="User signed out.")
        return Response({"detail": "You have been signed out."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        request.user.touch()
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        allowed = {"first_name", "last_name", "phone", "designation"}
        changed = [field for field in allowed if field in request.data]
        for field in changed:
            setattr(request.user, field, request.data[field])
        if changed:
            request.user.save(update_fields=changed)
        return Response(MeSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action("Changed password", "users", description="User changed their password.")
        return Response({"detail": "Your password has been updated."})


class DemoAccountsView(APIView):
    """
    Presentation helper: lists the seeded demo logins.

    Only available while ``DEMO_MODE`` is enabled, and it never exposes any
    account other than the fictional demo users created by ``seed_demo_data``.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        if not settings.DEMO_MODE:
            return Response(
                {"detail": "Demo accounts are disabled.", "code": "disabled"},
                status=status.HTTP_404_NOT_FOUND,
            )
        accounts = (
            User.objects.filter(is_demo=True)
            .exclude(role=RoleCode.SUPER_ADMIN)
            .order_by("role")
            .values("role", "email", "first_name", "last_name")
        )
        return Response(
            {
                "demo_mode": True,
                "password": settings.DEMO_PASSWORD,
                "notice": (
                    "These accounts and all data in this platform are fictional demo "
                    "data for local demonstration only."
                ),
                "accounts": [
                    {
                        "role": row["role"],
                        "role_label": dict(RoleCode.choices).get(row["role"], row["role"]),
                        "name": f"{row['first_name']} {row['last_name']}".strip(),
                        "email": row["email"],
                    }
                    for row in accounts
                ],
            }
        )


class UserViewSet(BaseViewSet):
    module = "users"
    queryset = User.objects.select_related("department").all()
    search_fields = ["username", "email", "first_name", "last_name", "employee_id"]
    ordering_fields = ["username", "email", "role", "date_joined", "last_login"]
    ordering = ["first_name", "last_name"]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return UserWriteSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdministrator()]
        return [ModulePermission()]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if role := params.get("role"):
            queryset = queryset.filter(role=role)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if params.get("is_active") in {"true", "false"}:
            queryset = queryset.filter(is_active=params["is_active"] == "true")
        return queryset


class RoleViewSet(viewsets.ViewSet):
    """Roles are seeded; administrators may adjust their permission matrix."""

    module = "users"

    def get_permissions(self):
        if self.action in {"update", "partial_update"}:
            return [IsAdministrator()]
        return [ModulePermission()]

    def list(self, request):
        counts = dict(User.objects.values_list("role").annotate(total=Count("id")))
        data = []
        for role in Role.objects.all():
            payload = RoleSerializer(role).data
            payload["user_count"] = counts.get(role.code, 0)
            data.append(payload)
        return Response({"count": len(data), "results": data})

    def retrieve(self, request, pk=None):
        role = Role.objects.get(pk=pk)
        payload = RoleSerializer(role).data
        payload["user_count"] = User.objects.filter(role=role.code).count()
        return Response(payload)

    def partial_update(self, request, pk=None):
        role = Role.objects.get(pk=pk)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(
            "Updated role permissions",
            "users",
            obj=role,
            description=f"Updated permissions for role {role.name}.",
        )
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def permission_catalogue(request):
    """Module/action catalogue powering the role editor UI."""
    return Response(
        {
            "modules": [
                {"code": code, "label": label} for code, label in MODULE_LABELS.items()
            ],
            "actions": ["view", "create", "edit", "delete"],
            "roles": [{"code": code, "label": label} for code, label in RoleCode.choices],
        }
    )
