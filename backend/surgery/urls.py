from rest_framework.routers import DefaultRouter

from .views import SurgeryViewSet

router = DefaultRouter()
router.register("", SurgeryViewSet, basename="surgery")

urlpatterns = router.urls
