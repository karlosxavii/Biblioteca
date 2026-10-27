from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "usuarios"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="usuarios/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.UsuarioListView.as_view(), name="list"),
    path("nuevo/", views.UsuarioCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="update"),
    path("<int:pk>/estado/", views.UsuarioToggleView.as_view(), name="toggle"),
]
