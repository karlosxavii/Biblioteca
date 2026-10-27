from django import forms
from django.utils import timezone

from catalogo.models import Ejemplar
from core.forms import StyledForm
from lectores.models import Lector

from .models import Prestamo

MAX_PRESTAMOS_ACTIVOS = 5


class PrestamoForm(StyledForm):
    lector = forms.ModelChoiceField(
        label="Lector",
        queryset=Lector.objects.none(),
        empty_label="Selecciona un lector",
    )
    fecha_prestamo = forms.DateField(
        label="Fecha de préstamo",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    fecha_entrega = forms.DateField(
        label="Fecha de entrega",
        initial=Prestamo.fecha_entrega_sugerida,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Fecha límite en la que el lector debe devolver los ejemplares.",
    )
    ejemplares = forms.ModelMultipleChoiceField(
        label="Ejemplares",
        queryset=Ejemplar.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lector"].queryset = Lector.objects.filter(activo=True).order_by(
            "apellidos", "nombres"
        )
        self.fields["lector"].label_from_instance = lambda lector: (
            f"{lector.codigo} · {lector.nombre_completo}"
        )
        disponibles = (
            Ejemplar.objects.disponibles()
            .select_related("libro")
            .order_by("libro__titulo", "codigo")
        )
        self.fields["ejemplares"].queryset = disponibles

    def clean(self):
        cleaned = super().clean()
        lector = cleaned.get("lector")
        fecha_prestamo = cleaned.get("fecha_prestamo")
        fecha_entrega = cleaned.get("fecha_entrega")
        ejemplares = cleaned.get("ejemplares")

        if fecha_prestamo and fecha_entrega and fecha_entrega < fecha_prestamo:
            self.add_error(
                "fecha_entrega",
                "La fecha de entrega no puede ser anterior a la fecha de préstamo.",
            )

        if lector:
            if not lector.activo:
                self.add_error("lector", "El lector está inactivo.")
            elif lector.prestamos_activos >= MAX_PRESTAMOS_ACTIVOS:
                self.add_error(
                    "lector",
                    f"El lector ya tiene {MAX_PRESTAMOS_ACTIVOS} préstamos activos.",
                )

        if ejemplares is not None:
            disponibles = set(
                Ejemplar.objects.disponibles()
                .filter(pk__in=[ejemplar.pk for ejemplar in ejemplares])
                .values_list("pk", flat=True)
            )
            no_disponibles = [
                ejemplar.codigo
                for ejemplar in ejemplares
                if ejemplar.pk not in disponibles
            ]
            if no_disponibles:
                self.add_error(
                    "ejemplares",
                    "Estos ejemplares ya no están disponibles: "
                    + ", ".join(no_disponibles),
                )

        return cleaned
