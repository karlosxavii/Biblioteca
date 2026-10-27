from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import GestionRequiredMixin

from .forms import AutorForm, EjemplarForm, LibroForm
from .models import Autor, Ejemplar, Libro


class ListaFiltradaMixin:
    paginate_by = 15

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["query"] = self.request.GET.get("q", "").strip()
        return contexto


class AutorListView(LoginRequiredMixin, ListaFiltradaMixin, ListView):
    model = Autor
    template_name = "catalogo/autor_list.html"
    context_object_name = "autores"

    def get_queryset(self):
        queryset = Autor.objects.annotate(total_libros=Count("libros", distinct=True))
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombres__icontains=query)
                | Q(apellidos__icontains=query)
                | Q(nacionalidad__icontains=query)
            )
        return queryset.order_by("apellidos", "nombres")


class AutorCreateView(GestionRequiredMixin, CreateView):
    model = Autor
    form_class = AutorForm
    template_name = "catalogo/autor_form.html"
    success_url = reverse_lazy("catalogo:autor_list")

    def form_valid(self, form):
        messages.success(self.request, "Autor creado correctamente.")
        return super().form_valid(form)


class AutorUpdateView(GestionRequiredMixin, UpdateView):
    model = Autor
    form_class = AutorForm
    template_name = "catalogo/autor_form.html"
    success_url = reverse_lazy("catalogo:autor_list")

    def form_valid(self, form):
        messages.success(self.request, "Autor actualizado correctamente.")
        return super().form_valid(form)


class AutorDeleteView(GestionRequiredMixin, DeleteView):
    model = Autor
    success_url = reverse_lazy("catalogo:autor_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre = self.object.nombre_completo
        try:
            self.object.delete()
            messages.success(request, f"Autor «{nombre}» eliminado correctamente.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar el autor porque tiene libros asociados.")
        return redirect(self.success_url)


class LibroListView(LoginRequiredMixin, ListaFiltradaMixin, ListView):
    model = Libro
    template_name = "catalogo/libro_list.html"
    context_object_name = "libros"

    def get_queryset(self):
        queryset = (
            Libro.objects.prefetch_related("autores")
            .annotate(
                num_ejemplares=Count("ejemplares", distinct=True),
                num_disponibles=Count(
                    "ejemplares",
                    filter=Q(ejemplares__estado=Ejemplar.Estado.DISPONIBLE),
                    distinct=True,
                ),
            )
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query)
                | Q(isbn__icontains=query)
                | Q(editorial__icontains=query)
                | Q(genero__icontains=query)
                | Q(autores__nombres__icontains=query)
                | Q(autores__apellidos__icontains=query)
            ).distinct()
        return queryset.order_by("titulo")


class LibroDetailView(LoginRequiredMixin, DetailView):
    model = Libro
    template_name = "catalogo/libro_detail.html"
    context_object_name = "libro"

    def get_queryset(self):
        return Libro.objects.prefetch_related(
            "autores",
            "ejemplares__detalles_prestamo__prestamo__lector",
        )


class LibroCreateView(GestionRequiredMixin, CreateView):
    model = Libro
    form_class = LibroForm
    template_name = "catalogo/libro_form.html"
    success_url = reverse_lazy("catalogo:libro_list")

    def form_valid(self, form):
        messages.success(self.request, "Libro creado correctamente.")
        return super().form_valid(form)


class LibroUpdateView(GestionRequiredMixin, UpdateView):
    model = Libro
    form_class = LibroForm
    template_name = "catalogo/libro_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Libro actualizado correctamente.")
        return super().form_valid(form)


class LibroDeleteView(GestionRequiredMixin, DeleteView):
    model = Libro
    success_url = reverse_lazy("catalogo:libro_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.ejemplares.filter(
            detalles_prestamo__fecha_devolucion__isnull=True
        ).exists():
            messages.error(
                request,
                "No se puede eliminar el libro porque tiene ejemplares prestados.",
            )
            return redirect(self.success_url)
        titulo = self.object.titulo
        try:
            self.object.delete()
            messages.success(request, f"Libro «{titulo}» eliminado correctamente.")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el libro porque tiene historial de préstamos.",
            )
        return redirect(self.success_url)


class EjemplarListView(LoginRequiredMixin, ListaFiltradaMixin, ListView):
    model = Ejemplar
    template_name = "catalogo/ejemplar_list.html"
    context_object_name = "ejemplares"

    def get_queryset(self):
        queryset = Ejemplar.objects.select_related("libro").prefetch_related(
            "detalles_prestamo"
        )
        query = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query)
                | Q(libro__titulo__icontains=query)
                | Q(ubicacion__icontains=query)
            )
        if estado in Ejemplar.Estado.values:
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["estados"] = Ejemplar.Estado.choices
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        return contexto


class EjemplarCreateView(GestionRequiredMixin, CreateView):
    model = Ejemplar
    form_class = EjemplarForm
    template_name = "catalogo/ejemplar_form.html"

    def get_initial(self):
        initial = super().get_initial()
        libro = self.request.GET.get("libro")
        if libro and libro.isdigit():
            initial["libro"] = libro
        return initial

    def get_success_url(self):
        messages.success(
            self.request,
            f"Ejemplar {self.object.codigo} registrado correctamente.",
        )
        return reverse_lazy("catalogo:libro_detail", args=[self.object.libro_id])


class EjemplarUpdateView(GestionRequiredMixin, UpdateView):
    model = Ejemplar
    form_class = EjemplarForm
    template_name = "catalogo/ejemplar_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Ejemplar actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("catalogo:libro_detail", args=[self.object.libro_id])


class EjemplarDeleteView(GestionRequiredMixin, DeleteView):
    model = Ejemplar
    success_url = reverse_lazy("catalogo:ejemplar_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.prestamo_activo:
            messages.error(
                request,
                "No se puede eliminar un ejemplar con préstamo activo.",
            )
            return redirect(self.success_url)
        codigo = self.object.codigo
        try:
            self.object.delete()
            messages.success(request, f"Ejemplar {codigo} eliminado correctamente.")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el ejemplar porque tiene historial de préstamos.",
            )
        return redirect(self.success_url)
