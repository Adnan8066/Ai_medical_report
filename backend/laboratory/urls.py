from rest_framework.routers import DefaultRouter

from .views import LabReportViewSet, LabTestViewSet

router = DefaultRouter()
router.register("tests", LabTestViewSet, basename="lab-test")
router.register("", LabReportViewSet, basename="lab-report")

urlpatterns = router.urls
