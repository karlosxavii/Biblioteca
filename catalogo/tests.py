from django.test import TestCase
from django.urls import reverse

from prestamos.services import crear_prestamo
from usuarios.models import Usuario

from .models import Autor, Ejemplar, Libro


class CatalogoModelTest(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(
            nombres="Gabriel",
            apellidos="García Márquez",
            nacionalidad="Colombiana",
        )
        self.libro = Libro.objects.create(
            titulo="Cien años de soledad",
            isbn="978-0307474728",
            editorial="Sudamericana",
            anio_publicacion=1967,
        )
        self.libro.autores.add(self.autor)
        self.ejemplar_1 = Ejemplar.objects.create(
            libro=self.libro,
            codigo="EJ-0001",
        )
        self.ejemplar_2 = Ejemplar.objects.create(
            libro=self.libro,
            codigo="EJ-0002",
        )

    def test_libro_autores_y_ejemplares(self):
        self.assertEqual(self.libro.autores.count(), 1)
        self.assertEqual(self.libro.total_ejemplares, 2)
        self.assertEqual(self.libro.ejemplares_disponibles, 2)
        self.assertEqual(self.autor.libros.count(), 1)

    def test_ejemplar_prestado_deja_de_estar_disponible(self):
        from lectores.models import Lector

        bibliotecario = Usuario.objects.create_user(
            username="biblio",
            password="clave123",
            rol=Usuario.Rol.BIBLIOTECARIO,
        )
        lector = Lector.objects.create(
            nombres="Ana",
            apellidos="Torres",
            documento="10203040",
        )
        crear_prestamo(
            lector=lector,
            bibliotecario=bibliotecario,
            fecha_prestamo=self.libro.creado.date(),
            fecha_entrega=self.libro.creado.date(),
            ejemplares=[self.ejemplar_1],
        )

        self.ejemplar_1.refresh_from_db()
        self.assertEqual(self.ejemplar_1.estado, Ejemplar.Estado.PRESTADO)
        self.assertEqual(
            list(Ejemplar.objects.disponibles().values_list("codigo", flat=True)),
            ["EJ-0002"],
        )
        self.assertEqual(self.libro.ejemplares_disponibles, 1)


class CatalogoPermisosTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="clave123",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
        )
        self.lector_user = Usuario.objects.create_user(
            username="lector",
            password="clave123",
            rol=Usuario.Rol.LECTOR,
        )
        self.autor = Autor.objects.create(nombres="Isabel", apellidos="Allende")

    def test_lector_puede_ver_catalogo(self):
        self.client.force_login(self.lector_user)
        self.assertEqual(
            self.client.get(reverse("catalogo:libro_list")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("catalogo:autor_list")).status_code,
            200,
        )

    def test_lector_no_puede_crear_autor(self):
        self.client.force_login(self.lector_user)
        response = self.client.get(reverse("catalogo:autor_create"))
        self.assertEqual(response.status_code, 403)

    def test_admin_crea_libro_con_autores(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalogo:libro_create"),
            {
                "titulo": "La casa de los espíritus",
                "isbn": "978-0525433477",
                "editorial": "Plaza & Janés",
                "anio_publicacion": "1982",
                "idioma": "ESPANOL",
                "genero": "Novela",
                "autores": [self.autor.pk],
                "sinopsis": "Saga familiar.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        libro = Libro.objects.get(isbn="978-0525433477")
        self.assertEqual(libro.autores.first(), self.autor)
