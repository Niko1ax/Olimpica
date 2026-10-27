
from django.db import models
from django.contrib.auth.models import User



class PerfilUsuario(models.Model):
    ROLES = [
        ("JUGADOR", "Jugador"),
        ("DUENIO", "Dueño de complejo"),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    rol = models.CharField(max_length=10, choices=ROLES)
    telefono = models.CharField(max_length=25, blank=True, default="")

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"


class Complejo(models.Model):
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    dueno = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name="complejos"
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Cancha(models.Model):
    SUPERFICIES = [
        ("CESPED_SINTETICO", "Césped sintético"),
        ("CEMENTO", "Cemento"),
        ("OTRA", "Otra"),
    ]

    complejo = models.ForeignKey(
        Complejo,
        on_delete=models.CASCADE,
        related_name="canchas"
    )
    nombre = models.CharField(max_length=100)
    superficie = models.CharField(
        max_length=20,
        choices=SUPERFICIES,
        default="CESPED_SINTETICO"
    )
    precio_por_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.complejo.nombre} - {self.nombre}"


class Reserva(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("CONFIRMADA", "Confirmada"),
        ("CANCELADA", "Cancelada"),
    ]

    jugador = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name="reservas"
    )
    cancha = models.ForeignKey(
        Cancha,
        on_delete=models.PROTECT,
        related_name="reservas"
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    estado = models.CharField(
        max_length=12,
        choices=ESTADOS,
        default="PENDIENTE"
    )
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return (
            f"Reserva #{self.pk} - {self.cancha} - "
            f"{self.fecha} {self.hora_inicio}"
        )


class Pago(models.Model):
    METODOS = [
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("MERCADO_PAGO", "Mercado Pago"),
        ("TARJETA", "Tarjeta"),
    ]

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
    ]

    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.PROTECT,
        related_name="pago"
    )
    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    metodo = models.CharField(max_length=20, choices=METODOS)
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="PENDIENTE"
    )
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Pago de reserva #{self.reserva_id} - {self.estado}"


class Resena(models.Model):
    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.CASCADE,
        related_name="resena"
    )
    puntuacion = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de reserva #{self.reserva_id}"

    def save(self, *args, **kwargs):
        if not 1 <= self.puntuacion <= 5:
            raise ValueError("La puntuación debe estar entre 1 y 5.")
        super().save(*args, **kwargs)
