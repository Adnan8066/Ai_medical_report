from django.db.models import Count, Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from audit.services import log_action
from config.viewsets import BaseViewSet
from users.permissions import IsAdministrator

from .models import Department, Floor, Hospital, MapLocation
from .serializers import (
    DepartmentSerializer,
    FloorSerializer,
    HospitalSerializer,
    MapLocationSerializer,
)


def get_hospital():
    """Return the singleton demo hospital, creating a stub if missing."""
    hospital = Hospital.objects.first()
    if hospital is None:
        hospital = Hospital.objects.create(
            name="AsterNova Multispeciality Hospital",
            city="Kochi",
            state="Kerala",
            country="India",
        )
    return hospital


class HospitalView(APIView):
    """Hospital profile and headline counts."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(HospitalSerializer(get_hospital()).data)

    def patch(self, request):
        """
        Update the hospital profile.

        Restricted to administrators; the audit log records who changed what.
        """
        if not request.user.is_administrator:
            return Response(
                {
                    "detail": "Only administrators can change hospital settings.",
                    "code": "permission_denied",
                    "errors": {},
                },
                status=403,
            )

        hospital = get_hospital()
        editable = {
            "name",
            "hospital_type",
            "established_year",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "phone",
            "emergency_number",
            "email",
            "website",
            "registration_number",
            "total_beds",
            "icu_beds",
            "emergency_beds",
            "about",
        }
        changed = []
        for field in editable:
            if field in request.data:
                setattr(hospital, field, request.data[field])
                changed.append(field)
        if changed:
            hospital.save(update_fields=changed + ["updated_at"])
            log_action(
                "Updated hospital settings",
                "hospital",
                obj=hospital,
                description="Updated {}".format(", ".join(sorted(changed))),
            )
        return Response(HospitalSerializer(hospital).data)


class SystemStatusView(APIView):
    """Runtime configuration shown on the settings screen."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from documents.services import ai, ocr

        return Response(
            {
                "demo_mode": settings.DEMO_MODE,
                "debug": settings.DEBUG,
                "database_engine": settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[-1],
                "time_zone": settings.TIME_ZONE,
                "ocr": ocr.ocr_status(),
                "ai": ai.answer_status(),
                "uploads": {
                    "max_size_mb": settings.MAX_UPLOAD_SIZE_MB,
                    "allowed_extensions": settings.ALLOWED_UPLOAD_EXTENSIONS,
                },
                "security": {
                    "jwt_access_minutes": int(
                        settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() // 60
                    ),
                    "jwt_refresh_days": settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].days,
                    "secure_ssl_redirect": getattr(settings, "SECURE_SSL_REDIRECT", False),
                    "audit_logging": True,
                },
            }
        )


class DepartmentViewSet(BaseViewSet):
    module = "departments"
    serializer_class = DepartmentSerializer
    search_fields = ["name", "code", "location", "description"]
    ordering_fields = ["name", "code", "bed_count"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = Department.objects.select_related("hod").prefetch_related(
            "doctors", "beds", "patients"
        )
        params = self.request.query_params
        if params.get("clinical") == "true":
            queryset = queryset.filter(is_clinical=True)
        if params.get("is_active") in {"true", "false"}:
            queryset = queryset.filter(is_active=params["is_active"] == "true")
        return queryset

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Department dashboard: staffing, beds and current load."""
        department = self.get_object()
        from admissions.models import Admission
        from doctors.models import Doctor
        from patients.models import Patient

        beds = department.beds.all()
        return Response(
            {
                "department": DepartmentSerializer(department).data,
                "doctors": Doctor.objects.filter(department=department).count(),
                "hods": Doctor.objects.filter(department=department, is_hod=True).count(),
                "patients": Patient.objects.filter(department=department).count(),
                "inpatients": Admission.objects.filter(
                    department=department,
                    status__in=[Admission.Status.ADMITTED, Admission.Status.UNDER_TREATMENT],
                ).count(),
                "beds": {
                    "total": beds.count(),
                    "available": beds.filter(status="available").count(),
                    "occupied": beds.filter(status="occupied").count(),
                    "reserved": beds.filter(status="reserved").count(),
                    "maintenance": beds.filter(status="maintenance").count(),
                },
            }
        )


class FloorViewSet(viewsets.ReadOnlyModelViewSet):
    module = "navigation"
    serializer_class = FloorSerializer
    queryset = Floor.objects.prefetch_related("locations").all()
    pagination_class = None


class MapLocationViewSet(viewsets.ReadOnlyModelViewSet):
    module = "navigation"
    serializer_class = MapLocationSerializer
    queryset = MapLocation.objects.select_related("floor", "department").all()
    pagination_class = None


class NavigationView(APIView):
    """
    Indoor wayfinding.

    Returns the searchable destination list plus a simple orthogonal route
    (a list of grid points) between two locations on the same floor.  Designed
    to be swapped for QR/Wi-Fi/AR positioning later - the API shape stays the
    same.
    """

    permission_classes = [IsAuthenticated]
    module = "navigation"

    def get(self, request):
        params = request.query_params
        query = (params.get("q") or "").strip()
        floor_number = params.get("floor")
        start_id = params.get("from")
        destination_id = params.get("to")

        locations = MapLocation.objects.select_related("floor", "department")
        if query:
            from django.db.models import Q

            locations = locations.filter(
                Q(name__icontains=query)
                | Q(code__icontains=query)
                | Q(description__icontains=query)
                | Q(keywords__icontains=query)
                | Q(department__name__icontains=query)
            )
        if floor_number:
            locations = locations.filter(floor__number=floor_number)

        payload = {
            "floors": FloorSerializer(
                Floor.objects.prefetch_related("locations").all(), many=True
            ).data,
            "destinations": MapLocationSerializer(locations, many=True).data,
            "route": None,
        }

        if destination_id:
            destination = MapLocation.objects.filter(pk=destination_id).first()
            start = (
                MapLocation.objects.filter(pk=start_id).first()
                if start_id
                else MapLocation.objects.filter(is_landmark=True).order_by("floor__number").first()
            )
            payload["route"] = self._build_route(start, destination)
        return Response(payload)

    @staticmethod
    def _build_route(start, destination):
        if start is None or destination is None:
            return None

        same_floor = start.floor_id == destination.floor_id
        points = [{"x": start.x, "y": start.y, "label": start.name}]
        if same_floor:
            # Simple orthogonal (Manhattan) path: move horizontally, then vertically.
            points.append({"x": destination.x, "y": start.y, "label": "corridor"})
            steps = [
                f"Head along the {start.floor.name} main corridor.",
                f"Turn towards {destination.name}.",
                f"Arrive at {destination.name} ({destination.description or destination.code}).",
            ]
        else:
            lift = MapLocation.objects.filter(
                category="facility", name__icontains="lift", floor=start.floor
            ).first()
            if lift:
                points.append({"x": lift.x, "y": lift.y, "label": "Lift lobby"})
            points.append(
                {"x": destination.x, "y": destination.y, "label": destination.name}
            )
            steps = [
                f"Follow the {start.floor.name} corridor to the lift lobby.",
                f"Take the lift to floor {destination.floor.number}.",
                f"Continue to {destination.name} ({destination.description or destination.code}).",
            ]
        points.append({"x": destination.x, "y": destination.y, "label": destination.name})

        distance = abs(destination.x - start.x) + abs(destination.y - start.y)
        return {
            "from": MapLocationSerializer(start).data,
            "to": MapLocationSerializer(destination).data,
            "same_floor": same_floor,
            "points": points,
            "steps": steps,
            "estimated_minutes": max(1, round(distance / 90)),
            "accessibility_note": (
                "Step-free route via lift available."
                if destination.is_wheelchair_accessible
                else "Please ask reception for an accessible alternative route."
            ),
            "notice": "Indoor navigation demo - signage and staff assistance take precedence.",
        }
