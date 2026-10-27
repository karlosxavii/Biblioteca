from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from core.mixins import AdministradorRequiredMixin

from .forms import UsuarioCreateForm, UsuarioEditForm
from .models import Usuario


class UsuarioListView(AdministradorRequiredMixin, ListView):
    model = Usuario
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"
    paginate_by = 15

    def get_queryset(self):
        queryset = Usuario.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(nombre_completo__icontains=query)
                | Q(email__icontains=query)
            )
        rol = self.request.GET.get("rol", "")
        if rol in Usuario.Rol.values:
            queryset = queryset.filter(rol=rol)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["query"] = self.request.GET.get("q", "").strip()
        contexto["rol_actual"] = self.request.GET.get("rol", "")
        contexto["roles"] = Usuario.Rol.choices
        return contexto


class UsuarioCreateView(AdministradorRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:list")

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class UsuarioUpdateView(AdministradorRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioEditForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:list")

    def form_valid(self, form):
        if self.object == self.request.user and not form.cleaned_data.get("is_active"):
            form.add_error("is_active", "No puedes desactivar tu propio usuario.")
            return self.form_invalid(form)
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)


class UsuarioToggleView(AdministradorRequiredMixin, View):
    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        if usuario == request.user:
            messages.error(request, "No puedes desactivar tu propio usuario.")
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=["is_active"])
            estado = "activado" if usuario.is_active else "desactivado"
            messages.success(
                request,
                f"Usuario {usuario.username} {estado} correctamente.",
            )
        return redirect("usuarios:list")
