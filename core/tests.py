from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Autor, Ejemplar, Libro
from lectores.models import Lector
from prestamos.services import crear_prestamo
from usuarios.models import Usuario


class NavegacionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(
            username="admin",
            password="clave123",
            nombre_completo="Administrador",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        cls.bibliotecario = Usuario.objects.create_user(
            username="biblio",
            password="clave123",
            nombre_completo="Bibliotecario",
            rol=Usuario.Rol.BIBLIOTECARIO,
        )
        cls.lector_user = Usuario.objects.create_user(
            username="lector",
            password="clave123",
            nombre_completo="Ana Torres",
            rol=Usuario.Rol.LECTOR,
        )
        cls.lector = Lector.objects.create(
            nombres="Ana",
            apellidos="Torres",
            documento="10203040",
            usuario=cls.lector_user,
        )
        cls.autor = Autor.objects.create(nombres="Gabriel", apellidos="García Márquez")
        cls.libro = Libro.objects.create(
            titulo="Cien años de soledad",
            isbn="978-0307474728",
            editorial="Sudamericana",
            anio_publicacion=1967,
        )
        cls.libro.autores.add(cls.autor)
        cls.ejemplar = Ejemplar.objects.create(libro=cls.libro, codigo="EJ-0001")
        cls.prestamo = crear_prestamo(
            lector=cls.lector,
            bibliotecario=cls.bibliotecario,
            fecha_prestamo=timezone.localdate(),
            fecha_entrega=timezone.localdate() + timedelta(days=7),
            ejemplares=[cls.ejemplar],
        )

    def test_admin_recorre_paginas_de_gestion(self):
        self.client.force_login(self.admin)
        urls = [
            reverse("core:dashboard"),
            f"{reverse('core:buscar')}?q=cien",
            reverse("catalogo:libro_list"),
            reverse("catalogo:libro_create"),
            reverse("catalogo:libro_detail", args=[self.libro.pk]),
            reverse("catalogo:libro_update", args=[self.libro.pk]),
            reverse("catalogo:autor_list"),
            reverse("catalogo:autor_create"),
            reverse("catalogo:autor_update", args=[self.autor.pk]),
            reverse("catalogo:ejemplar_list"),
            reverse("catalogo:ejemplar_create"),
            reverse("catalogo:ejemplar_update", args=[self.ejemplar.pk]),
            reverse("lectores:list"),
            reverse("lectores:create"),
            reverse("lectores:detail", args=[self.lector.pk]),
            reverse("lectores:update", args=[self.lector.pk]),
            reverse("prestamos:list"),
            reverse("prestamos:create"),
            reverse("prestamos:detail", args=[self.prestamo.pk]),
            reverse("usuarios:list"),
            reverse("usuarios:create"),
            reverse("usuarios:update", args=[self.admin.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_lector_recorre_sus_paginas(self):
        self.client.force_login(self.lector_user)
        urls = [
            reverse("core:dashboard"),
            reverse("catalogo:libro_list"),
            reverse("catalogo:libro_detail", args=[self.libro.pk]),
            reverse("catalogo:ejemplar_list"),
            reverse("prestamos:list"),
            reverse("prestamos:detail", args=[self.prestamo.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200, url)

        self.assertEqual(
            self.client.get(reverse("prestamos:create")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("lectores:list")).status_code,
            403,
        )

    def test_filtros_de_listados(self):
        self.client.force_login(self.admin)
        urls = [
            f"{reverse('catalogo:libro_list')}?q=cien",
            f"{reverse('catalogo:ejemplar_list')}?estado=PRESTADO",
            f"{reverse('lectores:list')}?estado=activos",
            f"{reverse('prestamos:list')}?estado=activos",
            f"{reverse('usuarios:list')}?rol=ADMINISTRADOR",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200, url)
