from rest_framework.routers import DefaultRouter

from .views import MedicineViewSet, PrescriptionViewSet

router = DefaultRouter()
router.register("prescriptions", PrescriptionViewSet, basename="prescription")
router.register("medicines", MedicineViewSet, basename="medicine")

urlpatterns = router.urls
