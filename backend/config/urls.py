"""Root URL configuration - every module is namespaced under /api/."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from analytics.views import GlobalSearchView


def health_check(_request):
    return JsonResponse({"status": "ok", "service": "AsterNova Hospital Intelligence Platform"})


urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    path("django-admin/", admin.site.urls),
    path("api/auth/", include("users.urls_auth")),
    path("api/users/", include("users.urls")),
    path("api/hospital/", include("hospital.urls")),
    path("api/departments/", include("hospital.urls_departments")),
    path("api/doctors/", include("doctors.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/appointments/", include("appointments.urls")),
    path("api/opd/", include("opd.urls")),
    path("api/emergency/", include("emergency.urls")),
    path("api/admissions/", include("admissions.urls")),
    path("api/beds/", include("beds.urls")),
    path("api/laboratory/", include("laboratory.urls")),
    path("api/radiology/", include("radiology.urls")),
    path("api/pharmacy/", include("pharmacy.urls")),
    path("api/surgery/", include("surgery.urls")),
    path("api/blood-bank/", include("bloodbank.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/ai/", include("ai_assistant.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/insurance/", include("insurance.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/staff/", include("staff.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/navigation/", include("hospital.urls_navigation")),
    path("api/search/", GlobalSearchView.as_view(), name="global-search"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
