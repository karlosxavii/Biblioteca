from django.db import models
from django.urls import reverse
from django.utils import timezone


class Autor(models.Model):
    nombres = models.CharField("Nombres", max_length=100)
    apellidos = models.CharField("Apellidos", max_length=100)
    nacionalidad = models.CharField("Nacionalidad", max_length=80, blank=True)
    fecha_nacimiento = models.DateField("Fecha de nacimiento", null=True, blank=True)
    biografia = models.TextField("Biografía", blank=True)

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autores"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def get_absolute_url(self):
        return reverse("catalogo:autor_list")


class Libro(models.Model):
    class Idioma(models.TextChoices):
        ESPANOL = "ESPANOL", "Español"
        INGLES = "INGLES", "Inglés"
        FRANCES = "FRANCES", "Francés"
        PORTUGUES = "PORTUGUES", "Portugués"
        OTRO = "OTRO", "Otro"

    titulo = models.CharField("Título", max_length=200)
    isbn = models.CharField("ISBN", max_length=20, unique=True)
    editorial = models.CharField("Editorial", max_length=120, blank=True)
    anio_publicacion = models.PositiveSmallIntegerField(
        "Año de publicación",
        null=True,
        blank=True,
    )
    idioma = models.CharField(
        "Idioma",
        max_length=20,
        choices=Idioma.choices,
        default=Idioma.ESPANOL,
    )
    genero = models.CharField("Género", max_length=80, blank=True)
    sinopsis = models.TextField("Sinopsis", blank=True)
    autores = models.ManyToManyField(
        Autor,
        related_name="libros",
        verbose_name="Autores",
    )
    creado = models.DateTimeField("Creado", auto_now_add=True)
    actualizado = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("catalogo:libro_detail", args=[self.pk])

    @property
    def autores_texto(self):
        return ", ".join(autor.nombre_completo for autor in self.autores.all())

    @property
    def total_ejemplares(self):
        return self.ejemplares.count()

    @property
    def ejemplares_disponibles(self):
        return self.ejemplares.disponibles().count()

    @property
    def tiene_disponibles(self):
        return self.ejemplares_disponibles > 0


class EjemplarQuerySet(models.QuerySet):
    def disponibles(self):
        from prestamos.models import DetallePrestamo

        prestados = DetallePrestamo.objects.filter(
            fecha_devolucion__isnull=True
        ).values("ejemplar_id")
        return self.filter(estado=Ejemplar.Estado.DISPONIBLE).exclude(pk__in=prestados)

    def prestados(self):
        return self.filter(estado=Ejemplar.Estado.PRESTADO)


class Ejemplar(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        PRESTADO = "PRESTADO", "Prestado"
        MANTENIMIENTO = "MANTENIMIENTO", "En mantenimiento"
        BAJA = "BAJA", "Dado de baja"

    libro = models.ForeignKey(
        Libro,
        on_delete=models.CASCADE,
        related_name="ejemplares",
        verbose_name="Libro",
    )
    codigo = models.CharField("Código de ejemplar", max_length=30, unique=True)
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
    )
    ubicacion = models.CharField("Ubicación", max_length=120, blank=True)
    fecha_alta = models.DateField("Fecha de alta", default=timezone.localdate)
    observaciones = models.TextField("Observaciones", blank=True)

    objects = EjemplarQuerySet.as_manager()

    class Meta:
        verbose_name = "Ejemplar"
        verbose_name_plural = "Ejemplares"
        ordering = ["libro__titulo", "codigo"]

    def __str__(self):
        return f"{self.codigo} · {self.libro.titulo}"

    def get_absolute_url(self):
        return reverse("catalogo:libro_detail", args=[self.libro_id])

    @property
    def disponibilidad_label(self):
        return self.get_estado_display()

    @property
    def prestamo_activo(self):
        return self.detalles_prestamo.filter(fecha_devolucion__isnull=True).first()

    @property
    def puede_prestarse(self):
        return self.estado == self.Estado.DISPONIBLE and self.prestamo_activo is None
