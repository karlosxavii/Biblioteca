from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.forms import StyledForm, StyledModelForm

from .models import Usuario


class LoginForm(StyledForm, AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "autofocus": True, "placeholder": "admin"}
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "••••••••"}
        ),
    )


class UsuarioCreateForm(StyledModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ["username", "nombre_completo", "email", "rol", "is_active"]
        labels = {"is_active": "Usuario activo"}

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if password1:
            try:
                validate_password(password1, self.instance)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario


class UsuarioEditForm(StyledModelForm):
    password1 = forms.CharField(
        label="Nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Déjala vacía para conservar la actual.",
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ["username", "nombre_completo", "email", "rol", "is_active"]
        labels = {"is_active": "Usuario activo"}

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            elif password1:
                try:
                    validate_password(password1, self.instance)
                except ValidationError as error:
                    self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            usuario.set_password(password)
        if commit:
            usuario.save()
        return usuario
