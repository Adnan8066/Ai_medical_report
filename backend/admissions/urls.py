from rest_framework.routers import DefaultRouter

from .views import AdmissionViewSet, DischargeSummaryViewSet

router = DefaultRouter()
router.register("discharge-summaries", DischargeSummaryViewSet, basename="discharge-summary")
router.register("", AdmissionViewSet, basename="admission")

urlpatterns = router.urls
