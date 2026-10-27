from django.contrib import messages
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import GestionRequiredMixin
from prestamos.models import Prestamo

from .forms import LectorForm
from .models import Lector


class LectorListView(GestionRequiredMixin, ListView):
    model = Lector
    template_name = "lectores/lector_list.html"
    context_object_name = "lectores"
    paginate_by = 15

    def get_queryset(self):
        queryset = Lector.objects.annotate(
            activos_ann=Count(
                "prestamos",
                filter=Q(prestamos__estado=Prestamo.Estado.ACTIVO),
                distinct=True,
            )
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombres__icontains=query)
                | Q(apellidos__icontains=query)
                | Q(documento__icontains=query)
                | Q(codigo__icontains=query)
                | Q(email__icontains=query)
            )
        estado = self.request.GET.get("estado", "")
        if estado == "activos":
            queryset = queryset.filter(activo=True)
        elif estado == "inactivos":
            queryset = queryset.filter(activo=False)
        return queryset.order_by("apellidos", "nombres")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["query"] = self.request.GET.get("q", "").strip()
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        return contexto


class LectorDetailView(GestionRequiredMixin, DetailView):
    model = Lector
    template_name = "lectores/lector_detail.html"
    context_object_name = "lector"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        prestamos = self.object.prestamos.select_related("lector").prefetch_related(
            "detalles__ejemplar"
        )
        contexto["prestamos"] = prestamos
        contexto["activos"] = prestamos.filter(estado=Prestamo.Estado.ACTIVO)
        contexto["historial"] = prestamos.exclude(estado=Prestamo.Estado.ACTIVO)
        return contexto


class LectorCreateView(GestionRequiredMixin, CreateView):
    model = Lector
    form_class = LectorForm
    template_name = "lectores/lector_form.html"

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(
            self.request,
            f"Lector {self.object.codigo} registrado correctamente.",
        )
        return respuesta

    def get_success_url(self):
        return reverse_lazy("lectores:detail", args=[self.object.pk])


class LectorUpdateView(GestionRequiredMixin, UpdateView):
    model = Lector
    form_class = LectorForm
    template_name = "lectores/lector_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Lector actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("lectores:detail", args=[self.object.pk])


class LectorDeleteView(GestionRequiredMixin, DeleteView):
    model = Lector
    success_url = reverse_lazy("lectores:list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.prestamos.exists():
            messages.error(
                request,
                "No se puede eliminar el lector porque tiene préstamos registrados.",
            )
            return redirect(self.success_url)
        nombre = self.object.nombre_completo
        try:
            self.object.delete()
            messages.success(request, f"Lector «{nombre}» eliminado correctamente.")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el lector porque tiene préstamos registrados.",
            )
        return redirect(self.success_url)
