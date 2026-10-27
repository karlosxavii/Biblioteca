from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        BIBLIOTECARIO = "BIBLIOTECARIO", "Bibliotecario"
        LECTOR = "LECTOR", "Lector"

    rol = models.CharField(
        "Rol",
        max_length=20,
        choices=Rol.choices,
        default=Rol.LECTOR,
    )
    nombre_completo = models.CharField("Nombre completo", max_length=150, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]

    def save(self, *args, **kwargs):
        if not self.nombre_completo:
            self.nombre_completo = self.get_full_name() or self.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre_completo} ({self.get_username()})"

    @property
    def rol_label(self):
        return self.get_rol_display()

    @property
    def es_administrador(self):
        return self.is_superuser or self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_bibliotecario(self):
        return self.rol == self.Rol.BIBLIOTECARIO

    @property
    def puede_gestionar(self):
        return self.es_administrador or self.es_bibliotecario

    @property
    def activo(self):
        return self.is_active

    @property
    def inicial(self):
        texto = self.nombre_completo or self.username
        return texto[:1].upper()
