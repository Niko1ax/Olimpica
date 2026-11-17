
from django.contrib import admin
from .models import (
    PerfilUsuario,
    Complejo,
    Cancha,
    Reserva,
    Pago,
    Resena,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol")
    list_filter = ("rol",)
    search_fields = ("usuario__username", "usuario__email")


@admin.register(Complejo)
class ComplejoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "telefono", "dueno")
    search_fields = ("nombre", "direccion")


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "complejo",
        "superficie",
        "precio_por_hora",
        "activa",
    )
    list_filter = ("superficie", "activa")
    search_fields = ("nombre", "complejo__nombre")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "jugador",
        "cancha",
        "fecha",
        "hora_inicio",
        "hora_fin",
        "estado",
    )
    list_filter = ("estado", "fecha")
    search_fields = (
        "jugador__usuario__username",
        "cancha__nombre",
        "cancha__complejo__nombre",
    )
    date_hierarchy = "fecha"


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reserva",
        "importe",
        "metodo",
        "estado",
    )
    list_filter = ("metodo", "estado")


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("id", "reserva", "puntuacion", "creada_en")
    list_filter = ("puntuacion",)
