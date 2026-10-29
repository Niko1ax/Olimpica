from django.utils.dateparse import parse_date
from django.db.models import Count, Sum, Q
from datetime import timedelta
from .models import Cancha, PerfilUsuario, Reserva
from datetime import datetime, time, timedelta
from .models import Cancha, Reserva

from .forms import CanchaForm
from .models import Cancha

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

    contexto = {
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "canchas": [],
        "busqueda_realizada": False,
        "error": "",
        "fecha_minima": timezone.localdate().isoformat(),
        "fecha_maxima": (
            timezone.localdate() + timedelta(days=365)
        ).isoformat(),
        "horarios": [
            f"{hora:02d}:00"
            for hora in range(10, 24)
        ],
    }

    if not fecha and not hora_inicio:
        return render(request, "reservas/buscar.html", contexto)

    if not fecha or not hora_inicio:
        contexto["error"] = "Elegí una fecha y una hora de inicio."
        return render(request, "reservas/buscar.html", contexto)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    except ValueError:
        contexto["error"] = "La fecha o el horario no son válidos."
        return render(request, "reservas/buscar.html", contexto)

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=365)

    if fecha_obj < hoy or fecha_obj > limite:
        contexto["error"] = (
            "Elegí una fecha entre hoy y los próximos 365 días."
        )
        return render(request, "reservas/buscar.html", contexto)

    if inicio_obj.minute != 0 or not (
        time(10, 0) <= inicio_obj <= time(23, 0)
    ):
        contexto["error"] = (
            "Los horarios disponibles comienzan cada hora, "
            "desde las 10:00 hasta las 23:00."
        )
        return render(request, "reservas/buscar.html", contexto)

    if fecha_obj == hoy and inicio_obj <= timezone.localtime().time().replace(
        tzinfo=None, second=0, microsecond=0
    ):
        contexto["error"] = "Elegí un horario que todavía no haya comenzado."
        return render(request, "reservas/buscar.html", contexto)

    fin_obj = (
        datetime.combine(fecha_obj, inicio_obj) + timedelta(hours=1)
    ).time()

    reservas_ocupadas = Reserva.objects.filter(
        cancha=OuterRef("pk"),
        fecha=fecha_obj,
        estado__in=["PENDIENTE", "CONFIRMADA"],
        hora_inicio__lt=fin_obj,
        hora_fin__gt=inicio_obj,
    )

    canchas_disponibles = (
        Cancha.objects.filter(
            activa=True,
            complejo__activo=True,
        )
        .annotate(horario_ocupado=Exists(reservas_ocupadas))
        .filter(horario_ocupado=False)
        .select_related("complejo")
        .order_by("complejo__nombre", "nombre")
    )

    contexto.update({
        "canchas": canchas_disponibles,
        "busqueda_realizada": True,
        "hora_fin": fin_obj.strftime("%H:%M"),
    })

    return render(request, "reservas/buscar.html", contexto)



@login_required
def reservar_cancha(request, cancha_id):
    cancha = get_object_or_404(
        Cancha.objects.select_related("complejo"),
        pk=cancha_id,
        activa=True,
        complejo__activo=True,
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
                "error": "Necesitás un perfil de jugador para reservar.",
            },
        )

    fecha = request.POST.get("fecha", request.GET.get("fecha", ""))
    hora_inicio = request.POST.get(
        "hora_inicio", request.GET.get("hora_inicio", "")
    )

    contexto = {
        "cancha": cancha,
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "error": "",
    }

    if request.method not in ["GET", "POST"]:
        return redirect("buscar_canchas")

    if not fecha or not hora_inicio:
        contexto["error"] = "Elegí una fecha y una hora de inicio."
        return render(request, "reservas/reservar.html", contexto)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    except ValueError:
        contexto["error"] = "La fecha o el horario no son válidos."
        return render(request, "reservas/reservar.html", contexto)

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=365)

    if fecha_obj < hoy or fecha_obj > limite:
        contexto["error"] = "Elegí una fecha entre hoy y los próximos 365 días."
        return render(request, "reservas/reservar.html", contexto)

    if inicio_obj.minute != 0 or not (
        time(10, 0) <= inicio_obj <= time(23, 0)
    ):
        contexto["error"] = "Elegí un horario entre las 10:00 y las 23:00, en punto."
        return render(request, "reservas/reservar.html", contexto)

    if fecha_obj == hoy and inicio_obj <= timezone.localtime().time().replace(
        tzinfo=None, second=0, microsecond=0
    ):
        contexto["error"] = "Elegí un horario que todavía no haya comenzado."
        return render(request, "reservas/reservar.html", contexto)

    inicio_dt = datetime.combine(fecha_obj, inicio_obj)
    fin_dt = inicio_dt + timedelta(hours=1)
    fin_obj = fin_dt.time()

    duracion = Decimal("1")
    precio_total = (
        cancha.precio_por_hora * duracion
    ).quantize(Decimal("0.01"))

    if request.method == "GET":
        contexto["hora_fin"] = fin_obj.strftime("%H:%M")
        contexto["precio_total"] = precio_total
        return render(request, "reservas/reservar.html", contexto)

    try:
        with transaction.atomic():
            # Revalidar el estado de la cancha dentro de la transacción.
            cancha_actual = get_object_or_404(
                Cancha.objects.select_related("complejo"),
                pk=cancha_id,
                activa=True,
                complejo__activo=True,
            )

            ocupada = Reserva.objects.filter(
                cancha=cancha_actual,
                fecha=fecha_obj,
                estado__in=["PENDIENTE", "CONFIRMADA"],
                hora_inicio__lt=fin_obj,
                hora_fin__gt=inicio_obj,
            ).exists()

            if ocupada:
                contexto["error"] = (
                    "Ese horario ya no está disponible. Elegí otro turno."
                )
                contexto["hora_fin"] = fin_obj.strftime("%H:%M")
                contexto["precio_total"] = precio_total
                return render(
                    request, "reservas/reservar.html", contexto
                )

            Reserva.objects.create(
                jugador=perfil,
                cancha=cancha_actual,
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
            {
                "reservas": [],
                "error": "Tu cuenta no tiene un perfil de jugador.",
            },
        )

    ahora = timezone.localtime()
    hoy = timezone.localdate()
    hora_actual = ahora.time().replace(tzinfo=None)

    reservas = (
        Reserva.objects.filter(
            jugador=perfil,
            estado__in=["PENDIENTE", "CONFIRMADA"],
        )
        .filter(
            fecha__gte=hoy,
        )
        .select_related("cancha", "cancha__complejo")
        .order_by("fecha", "hora_inicio")
    )

    # Si la reserva es para hoy, mostrarla solo si aún no terminó.
    reservas = [
        reserva for reserva in reservas
        if reserva.fecha > hoy or reserva.hora_fin > hora_actual
    ]

    return render(
        request,
        "reservas/mis_reservas.html",
        {
            "reservas": reservas,
            "error": "",
        },
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
def reportes(request):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO"
    ).first()

    if request.user.is_staff:
        reservas_base = Reserva.objects.all()
    elif perfil is not None:
        reservas_base = Reserva.objects.filter(
            cancha__complejo__dueno=perfil
        )
    else:
        return redirect("inicio")

    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    reservas = reservas_base.filter(
        fecha__gte=inicio_semana,
        fecha__lte=fin_semana
    ).select_related(
        "jugador",
        "jugador__usuario",
        "cancha",
        "cancha__complejo"
    ).order_by("fecha", "hora_inicio")

    resumen = reservas.aggregate(
        total=Count("id"),
        pendientes=Count(
            "id",
            filter=Q(estado="PENDIENTE")
        ),
        confirmadas=Count(
            "id",
            filter=Q(estado="CONFIRMADA")
        ),
        canceladas=Count(
            "id",
            filter=Q(estado="CANCELADA")
        ),
        recaudacion=Sum(
            "precio_total",
            filter=Q(estado="CONFIRMADA")
        )
    )

    return render(
        request,
        "reservas/reportes.html",
        {
            "reservas": reservas,
            "inicio_semana": inicio_semana,
            "fin_semana": fin_semana,
            "resumen": resumen,
        }
    )



@login_required
def actualizar_estado_reserva(request, reserva_id):
    if request.method != "POST":
        return redirect("panel_reservas")

    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if request.user.is_staff:
        reservas = Reserva.objects.all()
    elif perfil is not None:
        reservas = Reserva.objects.filter(
            cancha__complejo__dueno=perfil,
        )
    else:
        return redirect("inicio")

    reserva = get_object_or_404(reservas, pk=reserva_id)
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
    if request.user.is_staff:
        complejos = Complejo.objects.prefetch_related(
            "canchas"
        ).order_by("nombre")
    else:
        perfil = PerfilUsuario.objects.filter(
            usuario=request.user,
            rol="DUENIO",
        ).first()

        if perfil is None:
            return redirect("inicio")

        complejos = Complejo.objects.filter(
            dueno=perfil
        ).prefetch_related("canchas").order_by("nombre")

    return render(
        request,
        "reservas/administrar_complejos.html",
        {"complejos": complejos},
    )


@login_required
def crear_complejo(request):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    # El administrador puede gestionar complejos solo si
    # también tiene un perfil de dueño.
    if perfil is None:
        return render(
            request,
            "reservas/crear_complejo.html",
            {
                "formulario": ComplejoForm(),
                "error": (
                    "Tu usuario necesita un perfil de dueño "
                    "para registrar un complejo."
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


@login_required
def crear_cancha(request):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if perfil is None:
        return redirect("inicio")

    # El dueño solo puede elegir sus propios complejos.
    complejos_propios = Complejo.objects.filter(dueno=perfil)

    if request.method == "POST":
        formulario = CanchaForm(
            request.POST,
            user=request.user,
        )

        if formulario.is_valid():
            cancha = formulario.save(commit=False)

            # Comprobación adicional del propietario.
            if not complejos_propios.filter(
                pk=cancha.complejo_id
            ).exists():
                return redirect("inicio")

            cancha.save()
            return redirect("administrar_complejos")
    else:
        formulario = CanchaForm(user=request.user)

    return render(
        request,
        "reservas/crear_cancha.html",
        {"formulario": formulario},
    )



@login_required
def editar_complejo(request, complejo_id):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if perfil is None and not request.user.is_staff:
        return redirect("inicio")

    complejos = Complejo.objects.all()

    if not request.user.is_staff:
        complejos = complejos.filter(dueno=perfil)

    complejo = get_object_or_404(complejos, pk=complejo_id)

    if request.method == "POST":
        formulario = ComplejoForm(request.POST, instance=complejo)

        if formulario.is_valid():
            formulario.save()
            return redirect("administrar_complejos")
    else:
        formulario = ComplejoForm(instance=complejo)

    return render(
        request,
        "reservas/editar_complejo.html",
        {
            "formulario": formulario,
            "complejo": complejo,
        },
    )


@login_required
def cambiar_estado_complejo(request, complejo_id):
    if request.method != "POST":
        return redirect("administrar_complejos")

    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if perfil is None and not request.user.is_staff:
        return redirect("inicio")

    complejos = Complejo.objects.all()

    if not request.user.is_staff:
        complejos = complejos.filter(dueno=perfil)

    complejo = get_object_or_404(complejos, pk=complejo_id)
    complejo.activo = not complejo.activo
    complejo.save(update_fields=["activo"])

    return redirect("administrar_complejos")


@login_required
def editar_cancha(request, cancha_id):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if perfil is None and not request.user.is_staff:
        return redirect("inicio")

    canchas = Cancha.objects.select_related("complejo")

    if not request.user.is_staff:
        canchas = canchas.filter(complejo__dueno=perfil)

    cancha = get_object_or_404(canchas, pk=cancha_id)

    if request.method == "POST":
        formulario = CanchaForm(
            request.POST,
            instance=cancha,
            user=request.user,
        )

        if formulario.is_valid():
            cancha_editada = formulario.save(commit=False)

            if not request.user.is_staff:
                if cancha_editada.complejo.dueno_id != perfil.id:
                    return redirect("inicio")

            cancha_editada.save()
            return redirect("administrar_complejos")
    else:
        formulario = CanchaForm(
            instance=cancha,
            user=request.user,
        )

    return render(
        request,
        "reservas/editar_cancha.html",
        {
            "formulario": formulario,
            "cancha": cancha,
        },
    )


@login_required
def cambiar_estado_cancha(request, cancha_id):
    if request.method != "POST":
        return redirect("administrar_complejos")

    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO",
    ).first()

    if perfil is None and not request.user.is_staff:
        return redirect("inicio")

    canchas = Cancha.objects.select_related("complejo")

    if not request.user.is_staff:
        canchas = canchas.filter(complejo__dueno=perfil)

    cancha = get_object_or_404(canchas, pk=cancha_id)
    cancha.activa = not cancha.activa
    cancha.save(update_fields=["activa"])

    return redirect("administrar_complejos")

@login_required
def panel_reservas(request):
    perfil = PerfilUsuario.objects.filter(
        usuario=request.user,
        rol="DUENIO"
    ).first()

    if request.user.is_staff:
        reservas = Reserva.objects.all()
    elif perfil is not None:
        reservas = Reserva.objects.filter(
            cancha__complejo__dueno=perfil
        )
    else:
        return redirect("inicio")

    reservas = reservas.select_related(
        "jugador",
        "jugador__usuario",
        "cancha",
        "cancha__complejo"
    ).order_by("fecha", "hora_inicio")

    return render(
        request,
        "reservas/panel_reservas.html",
        {"reservas": reservas}
    )

