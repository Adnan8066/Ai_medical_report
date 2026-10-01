from django.urls import path

from .views import HospitalView, SystemStatusView

urlpatterns = [
    path("", HospitalView.as_view(), name="hospital-profile"),
    path("status/", SystemStatusView.as_view(), name="hospital-status"),
]
