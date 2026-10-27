from django.contrib import admin

from .models import DetallePrestamo, Prestamo


class DetallePrestamoInline(admin.TabularInline):
    model = DetallePrestamo
    extra = 0
    fields = ("ejemplar", "fecha_devolucion", "observaciones")
    autocomplete_fields = ("ejemplar",)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_admin",
        "lector",
        "bibliotecario",
        "fecha_prestamo",
        "fecha_entrega",
        "estado",
    )
    list_filter = ("estado", "fecha_prestamo", "fecha_entrega")
    search_fields = (
        "lector__nombres",
        "lector__apellidos",
        "lector__documento",
        "lector__codigo",
    )
    date_hierarchy = "fecha_prestamo"
    autocomplete_fields = ("lector", "bibliotecario")
    inlines = [DetallePrestamoInline]

    @admin.display(description="Código")
    def codigo_admin(self, obj):
        return obj.codigo


@admin.register(DetallePrestamo)
class DetallePrestamoAdmin(admin.ModelAdmin):
    list_display = ("prestamo", "ejemplar", "fecha_devolucion")
    list_filter = ("fecha_devolucion",)
    search_fields = ("prestamo__lector__nombres", "ejemplar__codigo")
    autocomplete_fields = ("prestamo", "ejemplar")
