from rest_framework.routers import DefaultRouter

from .views import ShiftAssignmentViewSet, ShiftViewSet, StaffViewSet

router = DefaultRouter()
router.register("shifts/assignments", ShiftAssignmentViewSet, basename="shift-assignment")
router.register("shifts", ShiftViewSet, basename="shift")
router.register("", StaffViewSet, basename="staff")

urlpatterns = router.urls
