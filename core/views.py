from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from catalogo.models import Ejemplar, Libro
from lectores.models import Lector
from prestamos.models import Prestamo


@login_required
def dashboard(request):
    usuario = request.user

    if usuario.puede_gestionar:
        hoy = timezone.localdate()
        prestamos = Prestamo.objects.select_related("lector", "bibliotecario")
        activos = prestamos.filter(estado=Prestamo.Estado.ACTIVO)
        resumen = {
            "libros": Libro.objects.count(),
            "ejemplares": Ejemplar.objects.count(),
            "disponibles": Ejemplar.objects.disponibles().count(),
            "lectores": Lector.objects.filter(activo=True).count(),
            "prestamos_activos": activos.count(),
            "vencidos": activos.filter(fecha_entrega__lt=hoy).count(),
        }
        contexto = {
            "es_gestion": True,
            "resumen": resumen,
            "recientes": prestamos[:8],
            "vencidos": activos.filter(fecha_entrega__lt=hoy).select_related("lector")[:8],
            "proximos": activos.filter(fecha_entrega__gte=hoy)
            .select_related("lector")
            .order_by("fecha_entrega")[:8],
        }
        return render(request, "core/dashboard.html", contexto)

    lector = getattr(usuario, "lector", None)
    prestamos = (
        Prestamo.objects.filter(lector=lector).select_related("lector")
        if lector
        else Prestamo.objects.none()
    )
    activos = prestamos.filter(estado=Prestamo.Estado.ACTIVO)
    resumen = {
        "activos": activos.count(),
        "vencidos": activos.filter(fecha_entrega__lt=timezone.localdate()).count(),
        "historial": prestamos.filter(estado=Prestamo.Estado.DEVUELTO).count(),
        "limite": 5,
    }
    contexto = {
        "es_gestion": False,
        "lector": lector,
        "resumen": resumen,
        "prestamos_activos": activos.select_related("lector"),
        "historial": prestamos.exclude(estado=Prestamo.Estado.ACTIVO)[:10],
    }
    return render(request, "core/dashboard_lector.html", contexto)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)


@login_required
def buscar(request):
    consulta = (request.GET.get("q") or "").strip()
    libros = []
    lectores = []
    prestamos = []
    if consulta and request.user.puede_gestionar:
        libros = Libro.objects.filter(
            Q(titulo__icontains=consulta)
            | Q(isbn__icontains=consulta)
            | Q(autores__nombres__icontains=consulta)
            | Q(autores__apellidos__icontains=consulta)
        ).distinct()[:10]
        lectores = Lector.objects.filter(
            Q(nombres__icontains=consulta)
            | Q(apellidos__icontains=consulta)
            | Q(documento__icontains=consulta)
            | Q(codigo__icontains=consulta)
        )[:10]
        if consulta.isdigit():
            prestamos = Prestamo.objects.filter(pk=int(consulta)).select_related("lector")
    elif consulta:
        libros = Libro.objects.filter(
            Q(titulo__icontains=consulta)
            | Q(isbn__icontains=consulta)
            | Q(autores__nombres__icontains=consulta)
            | Q(autores__apellidos__icontains=consulta)
        ).distinct()[:10]

    return render(
        request,
        "core/buscar.html",
        {
            "consulta": consulta,
            "libros": libros,
            "lectores": lectores,
            "prestamos": prestamos,
        },
    )
