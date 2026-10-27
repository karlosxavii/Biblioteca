from django.contrib import admin

from .models import Autor, Ejemplar, Libro


class EjemplarInline(admin.TabularInline):
    model = Ejemplar
    extra = 0
    fields = ("codigo", "estado", "ubicacion", "fecha_alta")


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nombres", "apellidos", "nacionalidad")
    search_fields = ("nombres", "apellidos", "nacionalidad")
    list_filter = ("nacionalidad",)


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "isbn", "editorial", "anio_publicacion", "idioma")
    search_fields = ("titulo", "isbn", "editorial", "autores__nombres", "autores__apellidos")
    list_filter = ("idioma", "genero")
    filter_horizontal = ("autores",)
    inlines = [EjemplarInline]


@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display = ("codigo", "libro", "estado", "ubicacion", "fecha_alta")
    list_filter = ("estado",)
    search_fields = ("codigo", "libro__titulo", "libro__isbn")
    autocomplete_fields = ("libro",)
