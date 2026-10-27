from django import forms

from core.forms import StyledModelForm

from .models import Autor, Ejemplar, Libro


class AutorForm(StyledModelForm):
    class Meta:
        model = Autor
        fields = [
            "nombres",
            "apellidos",
            "nacionalidad",
            "fecha_nacimiento",
            "biografia",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "biografia": forms.Textarea(attrs={"rows": 3}),
        }


class LibroForm(StyledModelForm):
    class Meta:
        model = Libro
        fields = [
            "titulo",
            "isbn",
            "editorial",
            "anio_publicacion",
            "idioma",
            "genero",
            "autores",
            "sinopsis",
        ]
        widgets = {
            "autores": forms.CheckboxSelectMultiple,
            "sinopsis": forms.Textarea(attrs={"rows": 4}),
        }


class EjemplarForm(StyledModelForm):
    class Meta:
        model = Ejemplar
        fields = [
            "libro",
            "codigo",
            "estado",
            "ubicacion",
            "fecha_alta",
            "observaciones",
        ]
        widgets = {
            "fecha_alta": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        estado = cleaned.get("estado")
        en_prestamo = bool(self.instance.pk and self.instance.prestamo_activo)

        if estado == Ejemplar.Estado.PRESTADO and not en_prestamo:
            self.add_error(
                "estado",
                "El estado Prestado se asigna automáticamente al registrar un préstamo.",
            )
        if en_prestamo and estado != Ejemplar.Estado.PRESTADO:
            self.add_error(
                "estado",
                "Este ejemplar tiene un préstamo activo; regístralo como devuelto primero.",
            )
        return cleaned
