from django.urls import path

from .views import ChartsView, DashboardView, ForecastView, GlobalSearchView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("charts/", ChartsView.as_view(), name="charts"),
    path("forecast/", ForecastView.as_view(), name="forecast"),
    path("search/", GlobalSearchView.as_view(), name="global-search"),
]
