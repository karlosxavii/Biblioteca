from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "nombre_completo",
        "email",
        "rol",
        "is_active",
        "is_staff",
    )
    list_filter = ("rol", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "nombre_completo", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Biblioteca", {"fields": ("rol", "nombre_completo")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Biblioteca", {"fields": ("rol", "nombre_completo", "email")}),
    )
