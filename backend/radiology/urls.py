from rest_framework.routers import DefaultRouter

from .views import RadiologyReportViewSet

router = DefaultRouter()
router.register("", RadiologyReportViewSet, basename="radiology-report")

urlpatterns = router.urls
