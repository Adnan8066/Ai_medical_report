from rest_framework.routers import DefaultRouter

from .views import BedViewSet, WardViewSet

router = DefaultRouter()
router.register("wards", WardViewSet, basename="ward")
router.register("", BedViewSet, basename="bed")

urlpatterns = router.urls
