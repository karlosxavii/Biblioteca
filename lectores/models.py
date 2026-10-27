from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone


class Lector(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="lector",
        verbose_name="Usuario de acceso",
        null=True,
        blank=True,
        limit_choices_to={"rol": "LECTOR"},
    )
    codigo = models.CharField("Código", max_length=20, unique=True, blank=True)
    nombres = models.CharField("Nombres", max_length=100)
    apellidos = models.CharField("Apellidos", max_length=100)
    documento = models.CharField("Documento de identidad", max_length=30, unique=True)
    email = models.EmailField("Correo electrónico", blank=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    direccion = models.CharField("Dirección", max_length=180, blank=True)
    activo = models.BooleanField("Activo", default=True)
    fecha_registro = models.DateField("Fecha de registro", default=timezone.localdate)

    class Meta:
        verbose_name = "Lector"
        verbose_name_plural = "Lectores"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.codigo} · {self.nombre_completo}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Lector.objects.aggregate(ultimo=Max("id"))["ultimo"] or 0
            self.codigo = f"LEC-{ultimo + 1:04d}"
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.usuario_id and self.usuario.rol != "LECTOR":
            raise ValidationError(
                {"usuario": "El usuario vinculado debe tener el rol Lector."}
            )

    def get_absolute_url(self):
        return reverse("lectores:detail", args=[self.pk])

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def prestamos_activos(self):
        return self.prestamos.filter(estado="ACTIVO").count()

    @property
    def tiene_prestamos_activos(self):
        return self.prestamos_activos > 0

    @property
    def puede_prestar(self):
        return self.activo and self.prestamos_activos < 5
