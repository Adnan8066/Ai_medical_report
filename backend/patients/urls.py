from rest_framework.routers import DefaultRouter

from .views import NurseAssignmentViewSet, PatientViewSet, VitalsViewSet

router = DefaultRouter()
router.register("vitals", VitalsViewSet, basename="vitals")
router.register("nurse-assignments", NurseAssignmentViewSet, basename="nurse-assignment")
router.register("", PatientViewSet, basename="patient")

urlpatterns = router.urls
