from django.contrib import admin
from django.urls import include, path

handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("catalogo/", include("catalogo.urls")),
    path("lectores/", include("lectores.urls")),
    path("prestamos/", include("prestamos.urls")),
    path("usuarios/", include("usuarios.urls")),
]
