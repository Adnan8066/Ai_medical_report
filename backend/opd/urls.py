from rest_framework.routers import DefaultRouter

from .views import OPDVisitViewSet

router = DefaultRouter()
router.register("", OPDVisitViewSet, basename="opd-visit")

urlpatterns = router.urls
