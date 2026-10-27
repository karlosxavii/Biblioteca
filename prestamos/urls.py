from django.urls import path

from . import views

app_name = "prestamos"

urlpatterns = [
    path("", views.PrestamoListView.as_view(), name="list"),
    path("nuevo/", views.PrestamoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PrestamoDetailView.as_view(), name="detail"),
    path(
        "<int:pk>/devolver/<int:detalle_id>/",
        views.DevolverEjemplarView.as_view(),
        name="return_copy",
    ),
    path("<int:pk>/cancelar/", views.CancelarPrestamoView.as_view(), name="cancel"),
]
