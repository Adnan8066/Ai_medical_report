from rest_framework.routers import DefaultRouter

from .views import BloodIssueViewSet, BloodStockViewSet, DonationViewSet

router = DefaultRouter()
router.register("stock", BloodStockViewSet, basename="blood-stock")
router.register("donations", DonationViewSet, basename="donation")
router.register("issues", BloodIssueViewSet, basename="blood-issue")

urlpatterns = router.urls
