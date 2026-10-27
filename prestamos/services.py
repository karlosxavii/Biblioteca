from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from catalogo.models import Ejemplar

from .models import DetallePrestamo, Prestamo


def crear_prestamo(
    *,
    lector,
    bibliotecario,
    fecha_prestamo,
    fecha_entrega,
    ejemplares,
    observaciones="",
):
    if not lector.activo:
        raise ValidationError("El lector seleccionado está inactivo.")
    if fecha_entrega < fecha_prestamo:
        raise ValidationError("La fecha de entrega no puede ser anterior al préstamo.")

    ejemplares = list(ejemplares)
    if not ejemplares:
        raise ValidationError("Debes seleccionar al menos un ejemplar.")

    with transaction.atomic():
        bloqueados = Ejemplar.objects.select_for_update().filter(
            pk__in=[ejemplar.pk for ejemplar in ejemplares]
        )
        disponibles = set(
            bloqueados.disponibles().values_list("pk", flat=True)
        )
        no_disponibles = [
            ejemplar.codigo
            for ejemplar in ejemplares
            if ejemplar.pk not in disponibles
        ]
        if no_disponibles:
            raise ValidationError(
                "Los siguientes ejemplares ya no están disponibles: "
                + ", ".join(no_disponibles)
            )

        prestamo = Prestamo.objects.create(
            lector=lector,
            bibliotecario=bibliotecario,
            fecha_prestamo=fecha_prestamo,
            fecha_entrega=fecha_entrega,
            observaciones=observaciones,
            estado=Prestamo.Estado.ACTIVO,
        )
        for ejemplar in ejemplares:
            DetallePrestamo.objects.create(prestamo=prestamo, ejemplar=ejemplar)
            ejemplar.estado = Ejemplar.Estado.PRESTADO
            ejemplar.save(update_fields=["estado"])

    return prestamo


def devolver_ejemplar(detalle, fecha=None):
    if detalle.fecha_devolucion:
        raise ValidationError("Este ejemplar ya fue devuelto.")

    fecha = fecha or timezone.localdate()
    with transaction.atomic():
        detalle.fecha_devolucion = fecha
        detalle.save(update_fields=["fecha_devolucion"])

        ejemplar = detalle.ejemplar
        ejemplar.estado = Ejemplar.Estado.DISPONIBLE
        ejemplar.save(update_fields=["estado"])

        prestamo = detalle.prestamo
        if not prestamo.detalles.filter(fecha_devolucion__isnull=True).exists():
            prestamo.estado = Prestamo.Estado.DEVUELTO
            prestamo.save(update_fields=["estado"])

    return detalle


def cancelar_prestamo(prestamo):
    if prestamo.estado != Prestamo.Estado.ACTIVO:
        raise ValidationError("Solo se pueden cancelar préstamos activos.")

    hoy = timezone.localdate()
    with transaction.atomic():
        for detalle in prestamo.detalles.filter(fecha_devolucion__isnull=True):
            detalle.fecha_devolucion = hoy
            detalle.save(update_fields=["fecha_devolucion"])
            ejemplar = detalle.ejemplar
            ejemplar.estado = Ejemplar.Estado.DISPONIBLE
            ejemplar.save(update_fields=["estado"])

        prestamo.estado = Prestamo.Estado.CANCELADO
        prestamo.save(update_fields=["estado"])

    return prestamo
