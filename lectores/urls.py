from django.urls import path

from . import views

app_name = "lectores"

urlpatterns = [
    path("", views.LectorListView.as_view(), name="list"),
    path("nuevo/", views.LectorCreateView.as_view(), name="create"),
    path("<int:pk>/", views.LectorDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.LectorUpdateView.as_view(), name="update"),
    path("<int:pk>/eliminar/", views.LectorDeleteView.as_view(), name="delete"),
]
