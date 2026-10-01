from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import RoleViewSet, UserViewSet, permission_catalogue

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")
router.register("", UserViewSet, basename="user")

urlpatterns = router.urls + [
    path("permissions/catalogue/", permission_catalogue, name="permission-catalogue"),
]
