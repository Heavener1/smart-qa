from django.contrib import admin
from django.urls import include, path

from core.views import ChatAPIView, DashboardAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/dashboard/", DashboardAPIView.as_view()),
    path("api/chat/", ChatAPIView.as_view()),
    path("api/", include("core.urls")),
]
