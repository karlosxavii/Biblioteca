from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class GestionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Solo administradores y bibliotecarios pueden gestionar el sistema."""

    def test_func(self):
        usuario = self.request.user
        return usuario.is_authenticated and usuario.puede_gestionar


class AdministradorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        usuario = self.request.user
        return usuario.is_authenticated and usuario.es_administrador
