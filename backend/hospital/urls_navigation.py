from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import FloorViewSet, MapLocationViewSet, NavigationView

router = DefaultRouter()
router.register("floors", FloorViewSet, basename="floor")
router.register("locations", MapLocationViewSet, basename="map-location")

urlpatterns = router.urls + [
    path("directions/", NavigationView.as_view(), name="navigation-directions"),
]
