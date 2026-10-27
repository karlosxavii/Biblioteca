from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from core.mixins import GestionRequiredMixin

from .forms import PrestamoForm
from .models import DetallePrestamo, Prestamo
from .services import cancelar_prestamo, crear_prestamo, devolver_ejemplar


class PrestamoListView(LoginRequiredMixin, ListView):
    model = Prestamo
    template_name = "prestamos/prestamo_list.html"
    context_object_name = "prestamos"
    paginate_by = 15

    def get_queryset(self):
        queryset = Prestamo.objects.select_related(
            "lector", "bibliotecario"
        ).prefetch_related("detalles__ejemplar")

        if not self.request.user.puede_gestionar:
            lector = getattr(self.request.user, "lector", None)
            queryset = queryset.filter(lector=lector) if lector else queryset.none()

        query = self.request.GET.get("q", "").strip()
        if query:
            filtros = (
                Q(lector__nombres__icontains=query)
                | Q(lector__apellidos__icontains=query)
                | Q(lector__documento__icontains=query)
                | Q(lector__codigo__icontains=query)
                | Q(detalles__ejemplar__codigo__icontains=query)
                | Q(detalles__ejemplar__libro__titulo__icontains=query)
            )
            if query.upper().startswith("PR-") and query[3:].isdigit():
                filtros |= Q(pk=int(query[3:]))
            elif query.isdigit():
                filtros |= Q(pk=int(query))
            queryset = queryset.filter(filtros).distinct()

        estado = self.request.GET.get("estado", "")
        hoy = timezone.localdate()
        if estado == "activos":
            queryset = queryset.filter(
                estado=Prestamo.Estado.ACTIVO, fecha_entrega__gte=hoy
            )
        elif estado == "vencidos":
            queryset = queryset.filter(
                estado=Prestamo.Estado.ACTIVO, fecha_entrega__lt=hoy
            )
        elif estado == "devueltos":
            queryset = queryset.filter(estado=Prestamo.Estado.DEVUELTO)
        elif estado == "cancelados":
            queryset = queryset.filter(estado=Prestamo.Estado.CANCELADO)

        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["query"] = self.request.GET.get("q", "").strip()
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        contexto["es_gestion"] = self.request.user.puede_gestionar
        return contexto


class PrestamoDetailView(LoginRequiredMixin, DetailView):
    model = Prestamo
    template_name = "prestamos/prestamo_detail.html"
    context_object_name = "prestamo"

    def get_queryset(self):
        queryset = Prestamo.objects.select_related(
            "lector", "bibliotecario"
        ).prefetch_related("detalles__ejemplar__libro")
        if not self.request.user.puede_gestionar:
            lector = getattr(self.request.user, "lector", None)
            queryset = queryset.filter(lector=lector) if lector else queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["es_gestion"] = self.request.user.puede_gestionar
        return contexto


class PrestamoCreateView(GestionRequiredMixin, FormView):
    form_class = PrestamoForm
    template_name = "prestamos/prestamo_form.html"

    def form_valid(self, form):
        datos = form.cleaned_data
        try:
            prestamo = crear_prestamo(
                lector=datos["lector"],
                bibliotecario=self.request.user,
                fecha_prestamo=datos["fecha_prestamo"],
                fecha_entrega=datos["fecha_entrega"],
                ejemplares=datos["ejemplares"],
                observaciones=datos.get("observaciones", ""),
            )
        except ValidationError as error:
            for mensaje in error.messages:
                form.add_error(None, mensaje)
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Préstamo {prestamo.codigo} registrado correctamente.",
        )
        return redirect("prestamos:detail", pk=prestamo.pk)


class DevolverEjemplarView(GestionRequiredMixin, View):
    def post(self, request, pk, detalle_id):
        prestamo = get_object_or_404(Prestamo, pk=pk)
        detalle = get_object_or_404(
            DetallePrestamo,
            pk=detalle_id,
            prestamo=prestamo,
        )
        try:
            devolver_ejemplar(detalle)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            messages.success(
                request,
                f"Ejemplar {detalle.ejemplar.codigo} devuelto correctamente.",
            )
        return redirect("prestamos:detail", pk=prestamo.pk)


class CancelarPrestamoView(GestionRequiredMixin, View):
    def post(self, request, pk):
        prestamo = get_object_or_404(Prestamo, pk=pk)
        try:
            cancelar_prestamo(prestamo)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            messages.success(request, f"Préstamo {prestamo.codigo} cancelado.")
        return redirect("prestamos:detail", pk=prestamo.pk)
