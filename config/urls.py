
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from reservas import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.inicio, name="inicio"),
    path("buscar/", views.buscar_canchas, name="buscar_canchas"),
    path("reservar/<int:cancha_id>/", views.reservar_cancha, name="reservar_cancha"),
    path("mis-reservas/", views.mis_reservas, name="mis_reservas"),

    # Inicio y cierre de sesión
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="reservas/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # Registro de jugadores
    path("registro/", views.registro, name="registro"),

    
    path(
        "reservas/<int:reserva_id>/cancelar/",
        views.cancelar_reserva,
        name="cancelar_reserva",
    ),

    
    path(
        "panel-reservas/",
        views.panel_reservas,
        name="panel_reservas",
    ),
    path(
        "panel-reservas/<int:reserva_id>/estado/",
        views.actualizar_estado_reserva,
        name="actualizar_estado_reserva",
    ),

        
    path(
        "administrar-complejos/",
        views.administrar_complejos,
        name="administrar_complejos",
    ),
    
    path(
        "crear-complejo/",
        views.crear_complejo,
        name="crear_complejo",
    ),

]
