from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("autores/", views.AutorListView.as_view(), name="autor_list"),
    path("autores/nuevo/", views.AutorCreateView.as_view(), name="autor_create"),
    path("autores/<int:pk>/editar/", views.AutorUpdateView.as_view(), name="autor_update"),
    path("autores/<int:pk>/eliminar/", views.AutorDeleteView.as_view(), name="autor_delete"),
    path("libros/", views.LibroListView.as_view(), name="libro_list"),
    path("libros/nuevo/", views.LibroCreateView.as_view(), name="libro_create"),
    path("libros/<int:pk>/", views.LibroDetailView.as_view(), name="libro_detail"),
    path("libros/<int:pk>/editar/", views.LibroUpdateView.as_view(), name="libro_update"),
    path("libros/<int:pk>/eliminar/", views.LibroDeleteView.as_view(), name="libro_delete"),
    path("ejemplares/", views.EjemplarListView.as_view(), name="ejemplar_list"),
    path("ejemplares/nuevo/", views.EjemplarCreateView.as_view(), name="ejemplar_create"),
    path("ejemplares/<int:pk>/editar/", views.EjemplarUpdateView.as_view(), name="ejemplar_update"),
    path("ejemplares/<int:pk>/eliminar/", views.EjemplarDeleteView.as_view(), name="ejemplar_delete"),
]
