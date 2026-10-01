from rest_framework.routers import DefaultRouter

from .views import MedicalDocumentViewSet

router = DefaultRouter()
router.register("", MedicalDocumentViewSet, basename="medical-document")

urlpatterns = router.urls
