
from django.contrib import admin
from django.urls import path
from reservas import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.inicio, name="inicio"),
]
