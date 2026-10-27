from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Ejemplar
from lectores.models import Lector


class Prestamo(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        DEVUELTO = "DEVUELTO", "Devuelto"
        CANCELADO = "CANCELADO", "Cancelado"

    lector = models.ForeignKey(
        Lector,
        on_delete=models.PROTECT,
        related_name="prestamos",
        verbose_name="Lector",
    )
    bibliotecario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="prestamos_gestionados",
        verbose_name="Bibliotecario",
    )
    fecha_prestamo = models.DateField("Fecha de préstamo", default=timezone.localdate)
    fecha_entrega = models.DateField("Fecha de entrega")
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )
    observaciones = models.TextField("Observaciones", blank=True)
    creado = models.DateTimeField("Creado", auto_now_add=True)

    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ["-fecha_prestamo", "-id"]

    def __str__(self):
        return f"{self.codigo} · {self.lector.nombre_completo}"

    def get_absolute_url(self):
        return reverse("prestamos:detail", args=[self.pk])

    @property
    def codigo(self):
        return f"PR-{self.pk:05d}" if self.pk else "PR-NUEVO"

    @property
    def esta_vencido(self):
        return self.estado == self.Estado.ACTIVO and self.fecha_entrega < timezone.localdate()

    @property
    def estado_efectivo(self):
        return "VENCIDO" if self.esta_vencido else self.estado

    @property
    def estado_efectivo_label(self):
        return dict(self.Estado.choices).get(self.estado_efectivo, self.estado_efectivo)

    @property
    def estado_badge(self):
        return {
            "ACTIVO": "badge-warning",
            "DEVUELTO": "badge-ok",
            "CANCELADO": "badge-muted",
            "VENCIDO": "badge-danger",
        }.get(self.estado_efectivo, "badge-muted")

    @property
    def dias_restantes(self):
        return (self.fecha_entrega - timezone.localdate()).days

    @property
    def dias_vencidos(self):
        return abs(min(self.dias_restantes, 0))

    @property
    def total_ejemplares(self):
        return self.detalles.count()

    @property
    def devueltos(self):
        return self.detalles.filter(fecha_devolucion__isnull=False).count()

    @property
    def pendientes(self):
        return self.detalles.filter(fecha_devolucion__isnull=True).count()

    @property
    def fecha_devolucion_final(self):
        return (
            self.detalles.filter(fecha_devolucion__isnull=False)
            .order_by("-fecha_devolucion")
            .values_list("fecha_devolucion", flat=True)
            .first()
        )

    @property
    def puede_devolverse(self):
        return self.estado == self.Estado.ACTIVO and self.detalles.filter(
            fecha_devolucion__isnull=True
        ).exists()

    @classmethod
    def fecha_entrega_sugerida(cls, dias: int = 7):
        return timezone.localdate() + timedelta(days=dias)


class DetallePrestamo(models.Model):
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Préstamo",
    )
    ejemplar = models.ForeignKey(
        Ejemplar,
        on_delete=models.PROTECT,
        related_name="detalles_prestamo",
        verbose_name="Ejemplar",
    )
    fecha_devolucion = models.DateField("Fecha de devolución", null=True, blank=True)
    observaciones = models.CharField("Observaciones", max_length=200, blank=True)

    class Meta:
        verbose_name = "Detalle de préstamo"
        verbose_name_plural = "Detalles de préstamo"
        ordering = ["ejemplar__codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["prestamo", "ejemplar"],
                name="prestamo_ejemplar_unico",
            )
        ]

    def __str__(self):
        return f"{self.prestamo.codigo} · {self.ejemplar.codigo}"

    @property
    def devuelto(self):
        return self.fecha_devolucion is not None

    @property
    def esta_vencido(self):
        return not self.devuelto and self.prestamo.fecha_entrega < timezone.localdate()

    @property
    def estado_label(self):
        if self.devuelto:
            return "Devuelto"
        return "Vencido" if self.esta_vencido else "Prestado"

    @property
    def estado_badge(self):
        if self.devuelto:
            return "badge-ok"
        return "badge-danger" if self.esta_vencido else "badge-warning"
