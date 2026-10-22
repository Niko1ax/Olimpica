from .models import PerfilUsuario, Complejo
from .forms import ComplejoForm
from .models import Reserva
from .forms import RegistroForm

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import redirect, render
from .models import PerfilUsuario

from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Cancha, Complejo, PerfilUsuario, Reserva

from datetime import datetime

from django.db.models import Exists, OuterRef
from django.shortcuts import render

from .models import Cancha, Complejo, Reserva


def inicio(request):
    complejos = Complejo.objects.all().prefetch_related("canchas")

    return render(
        request,
        "reservas/inicio.html",
        {"complejos": complejos},
    )


def buscar_canchas(request):
    fecha = request.GET.get("fecha", "")
    hora_inicio = request.GET.get("hora_inicio", "")
    hora_fin = request.GET.get("hora_fin", "")

    contexto = {
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "canchas": [],
        "busqueda_realizada": False,
        "error": "",
    }

    # Al entrar por primera vez, solo mostramos el formulario.
    if not fecha and not hora_inicio and not hora_fin:
        return render(request, "reservas/buscar.html", contexto)

    # Validar que se hayan completado los tres campos.
    if not fecha or not hora_inicio or not hora_fin:
        contexto["error"] = "Completá la fecha, la hora de inicio y la hora de fin."
        return render(request, "reservas/buscar.html", contexto)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
        fin_obj = datetime.strptime(hora_fin, "%H:%M").time()
    except ValueError:
        contexto["error"] = "La fecha o el horario ingresado no es válido."
        return render(request, "reservas/buscar.html", contexto)

    if fin_obj <= inicio_obj:
        contexto["error"] = "La hora de fin debe ser posterior a la hora de inicio."
        return render(request, "reservas/buscar.html", contexto)

    reservas_que_ocupan_horario = Reserva.objects.filter(
        cancha=OuterRef("pk"),
        fecha=fecha_obj,
        estado__in=["PENDIENTE", "CONFIRMADA"],
        hora_inicio__lt=fin_obj,
        hora_fin__gt=inicio_obj,
    )

    canchas_disponibles = (
        Cancha.objects.filter(activa=True)
        .annotate(
            horario_ocupado=Exists(reservas_que_ocupan_horario)
        )
        .filter(horario_ocupado=False)
        .select_related("complejo")
        .order_by("complejo__nombre", "nombre")
    )

    contexto["canchas"] = canchas_disponibles
    contexto["busqueda_realizada"] = True

    return render(request, "reservas/buscar.html", contexto)


@login_required
def reservar_cancha(request, cancha_id):
    cancha = get_object_or_404(
        Cancha.objects.select_related("complejo"),
        pk=cancha_id,
        activa=True,
    )

    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="JUGADOR",
    ).first()

    if perfil is None:
        return render(
            request,
            "reservas/reservar.html",
            {
                "cancha": cancha,
                "error": (
                    "Necesitás tener un perfil de jugador "
                    "para realizar una reserva."
                ),
            },
        )

    fecha = request.POST.get("fecha", request.GET.get("fecha", ""))
    hora_inicio = request.POST.get(
        "hora_inicio", request.GET.get("hora_inicio", "")
    )
    hora_fin = request.POST.get(
        "hora_fin", request.GET.get("hora_fin", "")
    )

    contexto = {
        "cancha": cancha,
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "error": "",
    }

    if request.method == "GET":
        return render(request, "reservas/reservar.html", contexto)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
        fin_obj = datetime.strptime(hora_fin, "%H:%M").time()
    except ValueError:
        contexto["error"] = "Ingresá una fecha y horarios válidos."
        return render(request, "reservas/reservar.html", contexto)

    if fin_obj <= inicio_obj:
        contexto["error"] = "La hora de fin debe ser posterior al inicio."
        return render(request, "reservas/reservar.html", contexto)

    if fecha_obj < timezone.localdate():
        contexto["error"] = "No podés reservar una fecha pasada."
        return render(request, "reservas/reservar.html", contexto)

    if fecha_obj == timezone.localdate():
        ahora = timezone.localtime().time().replace(tzinfo=None)
        if inicio_obj <= ahora:
            contexto["error"] = "Elegí un horario futuro."
            return render(request, "reservas/reservar.html", contexto)

    duracion = (
        datetime.combine(fecha_obj, fin_obj)
        - datetime.combine(fecha_obj, inicio_obj)
    ).total_seconds() / 3600

    precio_total = (
        cancha.precio_por_hora * Decimal(str(duracion))
    ).quantize(Decimal("0.01"))

    try:
        with transaction.atomic():
            ocupada = Reserva.objects.filter(
                cancha=cancha,
                fecha=fecha_obj,
                estado__in=["PENDIENTE", "CONFIRMADA"],
                hora_inicio__lt=fin_obj,
                hora_fin__gt=inicio_obj,
            ).exists()

            if ocupada:
                contexto["error"] = (
                    "Ese horario ya no está disponible. "
                    "Volvé al buscador y elegí otro."
                )
                return render(request, "reservas/reservar.html", contexto)

            reserva = Reserva.objects.create(
                jugador=perfil,
                cancha=cancha,
                fecha=fecha_obj,
                hora_inicio=inicio_obj,
                hora_fin=fin_obj,
                precio_total=precio_total,
                estado="PENDIENTE",
            )

    except Exception:
        contexto["error"] = (
            "No se pudo registrar la reserva. Intentá nuevamente."
        )
        return render(request, "reservas/reservar.html", contexto)

    return redirect("mis_reservas")


@login_required
def mis_reservas(request):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="JUGADOR",
    ).first()

    if perfil is None:
        return render(
            request,
            "reservas/mis_reservas.html",
            {"reservas": [], "error": "Tu cuenta no tiene un perfil de jugador."},
        )

    reservas = (
        Reserva.objects.filter(jugador=perfil)
        .select_related("cancha", "cancha__complejo")
        .order_by("-fecha", "-hora_inicio")
    )

    return render(
        request,
        "reservas/mis_reservas.html",
        {"reservas": reservas, "error": ""},
    )



def registro(request):
    if request.method == "POST":
        formulario = RegistroForm(request.POST)

        if formulario.is_valid():
            with transaction.atomic():
                usuario = formulario.save()

                PerfilUsuario.objects.create(
                    usuario=usuario,
                    rol="JUGADOR",
                    telefono=formulario.cleaned_data["telefono"],
                )

            login(request, usuario)
            return redirect("buscar_canchas")
    else:
        formulario = RegistroForm()

    return render(
        request,
        "reservas/registro.html",
        {"formulario": formulario},
    )

@login_required
def cancelar_reserva(request, reserva_id):
    if request.method != "POST":
        return redirect("mis_reservas")

    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="JUGADOR",
    ).first()

    if perfil is None:
        return redirect("mis_reservas")

    reserva = get_object_or_404(
        Reserva,
        pk=reserva_id,
        jugador=perfil,
    )

    if reserva.estado not in ["PENDIENTE", "CONFIRMADA"]:
        return redirect("mis_reservas")

    ahora = timezone.localtime()
    inicio_reserva = timezone.make_aware(
        datetime.combine(reserva.fecha, reserva.hora_inicio),
        timezone.get_current_timezone(),
    )

    if inicio_reserva <= ahora:
        return redirect("mis_reservas")

    reserva.estado = "CANCELADA"
    reserva.save(update_fields=["estado"])

    return redirect("mis_reservas")


@login_required
def panel_reservas(request):
    # Solo el personal autorizado puede acceder al panel.
    if not request.user.is_staff:
        return redirect("inicio")

    reservas = Reserva.objects.select_related(
        "jugador",
        "jugador__usuario",
        "cancha",
        "cancha__complejo",
    ).order_by("-fecha", "-hora_inicio")

    return render(
        request,
        "reservas/panel_reservas.html",
        {"reservas": reservas},
    )


@login_required
def actualizar_estado_reserva(request, reserva_id):
    # Solo el personal autorizado puede cambiar estados.
    if not request.user.is_staff:
        return redirect("inicio")

    if request.method != "POST":
        return redirect("panel_reservas")

    reserva = get_object_or_404(Reserva, pk=reserva_id)
    nuevo_estado = request.POST.get("estado")

    estados_permitidos = {
        "PENDIENTE",
        "CONFIRMADA",
        "CANCELADA",
    }

    if nuevo_estado in estados_permitidos:
        reserva.estado = nuevo_estado
        reserva.save(update_fields=["estado"])

    return redirect("panel_reservas")


@login_required
def administrar_complejos(request):
    if not request.user.is_staff:
        return redirect("inicio")

    complejos = Complejo.objects.prefetch_related("canchas").order_by("nombre")

    return render(
        request,
        "reservas/administrar_complejos.html",
        {"complejos": complejos},
    )


@login_required
def crear_complejo(request):
    if not request.user.is_staff:
        return redirect("inicio")

    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if perfil is None:
        return render(
            request,
            "reservas/crear_complejo.html",
            {
                "formulario": ComplejoForm(),
                "error": (
                    "Tu cuenta administradora necesita un perfil "
                    "de dueño para crear complejos."
                ),
            },
        )

    if request.method == "POST":
        formulario = ComplejoForm(request.POST)

        if formulario.is_valid():
            complejo = formulario.save(commit=False)
            complejo.dueno = perfil
            complejo.save()
            return redirect("administrar_complejos")
    else:
        formulario = ComplejoForm()

    return render(
        request,
        "reservas/crear_complejo.html",
        {"formulario": formulario, "error": ""},
    )
