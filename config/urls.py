
from django.contrib import admin
from django.urls import path
from reservas import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.inicio, name="inicio"),
    path("buscar/", views.buscar_canchas, name="buscar_canchas"),
    path(
        "reservar/<int:cancha_id>/",
        views.reservar_cancha,
        name="reservar_cancha",
    ),
    path(
        "mis-reservas/",
        views.mis_reservas,
        name="mis_reservas",
    ),
]
