from django import forms
from django.db.models import Q

from core.forms import StyledModelForm
from usuarios.models import Usuario

from .models import Lector


class LectorForm(StyledModelForm):
    class Meta:
        model = Lector
        fields = [
            "usuario",
            "nombres",
            "apellidos",
            "documento",
            "email",
            "telefono",
            "direccion",
            "activo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filtro = Q(rol=Usuario.Rol.LECTOR)
        if self.instance.pk and self.instance.usuario_id:
            filtro |= Q(pk=self.instance.usuario_id)
        usuarios = Usuario.objects.filter(filtro)
        vinculados = Lector.objects.exclude(pk=self.instance.pk).exclude(
            usuario__isnull=True
        )
        usuarios = usuarios.exclude(pk__in=vinculados.values_list("usuario_id", flat=True))
        self.fields["usuario"].queryset = usuarios.order_by("nombre_completo", "username")
        self.fields["usuario"].label_from_instance = lambda usuario: (
            f"{usuario.nombre_completo} ({usuario.username})"
        )
        self.fields["usuario"].help_text = (
            "Opcional. Permite que el lector consulte sus propios préstamos."
        )
