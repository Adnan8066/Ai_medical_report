from datetime import date

from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseReadOnlyViewSet, BaseViewSet

from .models import Shift, ShiftAssignment, Staff
from .serializers import ShiftAssignmentSerializer, ShiftSerializer, StaffSerializer


class StaffViewSet(BaseViewSet):
    module = "staff"
    queryset = Staff.objects.select_related("department", "shift").all()
    serializer_class = StaffSerializer
    search_fields = ["name", "employee_id", "designation", "contact", "email"]
    ordering_fields = ["name", "joining_date", "employee_id"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if role := params.get("role"):
            queryset = queryset.filter(role=role)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if status := params.get("status"):
            queryset = queryset.filter(status=status)
        if shift := params.get("shift"):
            queryset = queryset.filter(shift_id=shift)
        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        by_role = list(
            Staff.objects.values("role").annotate(total=Count("id")).order_by("-total")
        )
        return Response(
            {
                "total": Staff.objects.count(),
                "active": Staff.objects.filter(status=Staff.Status.ACTIVE).count(),
                "on_duty": Staff.objects.filter(status=Staff.Status.ON_DUTY).count(),
                "by_role": [
                    {
                        "role": row["role"],
                        "label": dict(Staff.Role.choices).get(row["role"], row["role"]),
                        "total": row["total"],
                    }
                    for row in by_role
                ],
            }
        )


class ShiftViewSet(BaseReadOnlyViewSet):
    module = "staff"
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    pagination_class = None


class ShiftAssignmentViewSet(BaseViewSet):
    module = "staff"
    queryset = ShiftAssignment.objects.select_related(
        "staff", "shift", "department"
    ).all()
    serializer_class = ShiftAssignmentSerializer
    ordering = ["-date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if target := params.get("date"):
            queryset = queryset.filter(date=target)
        elif params.get("today") == "true":
            queryset = queryset.filter(date=date.today())
        if shift := params.get("shift"):
            queryset = queryset.filter(shift_id=shift)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if staff := params.get("staff"):
            queryset = queryset.filter(staff_id=staff)
        return queryset

    @action(detail=False, methods=["get"])
    def roster(self, request):
        """Today's roster grouped by shift for the shift board screen."""
        target = request.query_params.get("date") or date.today().isoformat()
        assignments = self.get_queryset().filter(date=target)
        grouped = []
        for shift in Shift.objects.all():
            rows = [a for a in assignments if a.shift_id == shift.id]
            grouped.append(
                {
                    "shift": ShiftSerializer(shift).data,
                    "assignments": ShiftAssignmentSerializer(rows, many=True).data,
                    "count": len(rows),
                }
            )
        return Response({"date": target, "shifts": grouped})
