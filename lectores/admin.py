from django.contrib import admin

from .models import Lector


@admin.register(Lector)
class LectorAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombres",
        "apellidos",
        "documento",
        "email",
        "activo",
        "usuario",
    )
    list_filter = ("activo",)
    search_fields = (
        "codigo",
        "nombres",
        "apellidos",
        "documento",
        "email",
        "usuario__username",
    )
    autocomplete_fields = ("usuario",)
