from rest_framework.routers import DefaultRouter

from .views import EmergencyVisitViewSet

router = DefaultRouter()
router.register("", EmergencyVisitViewSet, basename="emergency-visit")

urlpatterns = router.urls
