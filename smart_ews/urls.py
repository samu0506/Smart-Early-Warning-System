from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Students app handles root "/"
    path("", include("students.urls")),
]
