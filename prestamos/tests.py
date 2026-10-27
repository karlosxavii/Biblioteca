from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Autor, Ejemplar, Libro
from lectores.models import Lector
from usuarios.models import Usuario

from .models import DetallePrestamo, Prestamo
from .services import crear_prestamo


class PrestamoBaseTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="clave123",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.bibliotecario = Usuario.objects.create_user(
            username="biblio",
            password="clave123",
            rol=Usuario.Rol.BIBLIOTECARIO,
        )
        self.lector_user = Usuario.objects.create_user(
            username="lector",
            password="clave123",
            rol=Usuario.Rol.LECTOR,
        )
        self.lector = Lector.objects.create(
            nombres="Ana",
            apellidos="Torres",
            documento="10203040",
            usuario=self.lector_user,
        )
        self.lector_2 = Lector.objects.create(
            nombres="Carlos",
            apellidos="Ruiz",
            documento="99887766",
        )
        self.autor = Autor.objects.create(nombres="Gabriel", apellidos="García Márquez")
        self.libro = Libro.objects.create(
            titulo="Cien años de soledad",
            isbn="978-0307474728",
        )
        self.libro.autores.add(self.autor)
        self.ejemplar_1 = Ejemplar.objects.create(libro=self.libro, codigo="EJ-0001")
        self.ejemplar_2 = Ejemplar.objects.create(libro=self.libro, codigo="EJ-0002")
        self.hoy = timezone.localdate()

    def crear_prestamo_demo(
        self,
        lector=None,
        ejemplares=None,
        fecha_prestamo=None,
        fecha_entrega=None,
    ):
        return crear_prestamo(
            lector=lector or self.lector,
            bibliotecario=self.bibliotecario,
            fecha_prestamo=fecha_prestamo or self.hoy,
            fecha_entrega=fecha_entrega or self.hoy + timedelta(days=7),
            ejemplares=ejemplares or [self.ejemplar_1],
        )


class PrestamoServiceTest(PrestamoBaseTest):
    def test_crear_prestamo_marca_ejemplares_prestados(self):
        prestamo = self.crear_prestamo_demo(
            ejemplares=[self.ejemplar_1, self.ejemplar_2]
        )

        self.assertEqual(prestamo.estado, Prestamo.Estado.ACTIVO)
        self.assertEqual(prestamo.total_ejemplares, 2)
        self.assertEqual(prestamo.pendientes, 2)
        self.assertEqual(prestamo.codigo, f"PR-{prestamo.pk:05d}")

        self.ejemplar_1.refresh_from_db()
        self.ejemplar_2.refresh_from_db()
        self.assertEqual(self.ejemplar_1.estado, Ejemplar.Estado.PRESTADO)
        self.assertEqual(self.ejemplar_2.estado, Ejemplar.Estado.PRESTADO)
        self.assertEqual(self.lector.prestamos_activos, 1)

    def test_prestamo_vencido(self):
        prestamo = self.crear_prestamo_demo(
            fecha_prestamo=self.hoy - timedelta(days=10),
            fecha_entrega=self.hoy - timedelta(days=3),
        )
        self.assertTrue(prestamo.esta_vencido)
        self.assertEqual(prestamo.estado_efectivo, "VENCIDO")

    def test_no_permite_doble_prestamo_de_ejemplar(self):
        self.crear_prestamo_demo(ejemplares=[self.ejemplar_1])
        with self.assertRaisesMessage(Exception, "ya no están disponibles"):
            self.crear_prestamo_demo(
                lector=self.lector_2,
                ejemplares=[self.ejemplar_1],
            )

    def test_lector_inactivo_no_puede_prestar(self):
        self.lector.activo = False
        self.lector.save(update_fields=["activo"])
        with self.assertRaisesMessage(Exception, "inactivo"):
            self.crear_prestamo_demo()


class PrestamoViewsTest(PrestamoBaseTest):
    def test_registrar_prestamo_por_post(self):
        self.client.force_login(self.bibliotecario)
        response = self.client.post(
            reverse("prestamos:create"),
            {
                "lector": self.lector.pk,
                "fecha_prestamo": self.hoy.isoformat(),
                "fecha_entrega": (self.hoy + timedelta(days=7)).isoformat(),
                "ejemplares": [self.ejemplar_1.pk, self.ejemplar_2.pk],
                "observaciones": "Prueba",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "registrado correctamente")
        prestamo = Prestamo.objects.get()
        self.assertEqual(prestamo.detalles.count(), 2)

    def test_no_permite_prestar_ejemplar_ocupado(self):
        self.crear_prestamo_demo(ejemplares=[self.ejemplar_1])
        self.client.force_login(self.bibliotecario)
        response = self.client.post(
            reverse("prestamos:create"),
            {
                "lector": self.lector_2.pk,
                "fecha_prestamo": self.hoy.isoformat(),
                "fecha_entrega": (self.hoy + timedelta(days=7)).isoformat(),
                "ejemplares": [self.ejemplar_1.pk],
                "observaciones": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("ejemplares", response.context["form"].errors)
        self.assertEqual(Prestamo.objects.count(), 1)

    def test_devolucion_individual_cierra_prestamo(self):
        prestamo = self.crear_prestamo_demo(
            ejemplares=[self.ejemplar_1, self.ejemplar_2]
        )
        detalle_1, detalle_2 = prestamo.detalles.order_by("pk")
        self.client.force_login(self.bibliotecario)

        response = self.client.post(
            reverse(
                "prestamos:return_copy",
                args=[prestamo.pk, detalle_1.pk],
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        detalle_1.refresh_from_db()
        self.assertEqual(detalle_1.fecha_devolucion, self.hoy)
        self.ejemplar_1.refresh_from_db()
        self.assertEqual(self.ejemplar_1.estado, Ejemplar.Estado.DISPONIBLE)
        prestamo.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.Estado.ACTIVO)

        self.client.post(
            reverse(
                "prestamos:return_copy",
                args=[prestamo.pk, detalle_2.pk],
            )
        )
        prestamo.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.Estado.DEVUELTO)
        self.assertEqual(prestamo.devueltos, 2)

    def test_lector_solo_ve_sus_prestamos(self):
        propio = self.crear_prestamo_demo()
        ajeno = self.crear_prestamo_demo(
            lector=self.lector_2,
            ejemplares=[self.ejemplar_2],
        )
        self.client.force_login(self.lector_user)

        response = self.client.get(reverse("prestamos:list"))
        self.assertContains(response, propio.codigo)
        self.assertNotContains(response, ajeno.codigo)

        self.assertEqual(
            self.client.get(
                reverse("prestamos:detail", args=[ajeno.pk])
            ).status_code,
            404,
        )

    def test_lector_no_puede_crear_prestamo(self):
        self.client.force_login(self.lector_user)
        response = self.client.get(reverse("prestamos:create"))
        self.assertEqual(response.status_code, 403)

    def test_cancelar_prestamo_libera_ejemplares(self):
        prestamo = self.crear_prestamo_demo(ejemplares=[self.ejemplar_1])
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("prestamos:cancel", args=[prestamo.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        prestamo.refresh_from_db()
        self.ejemplar_1.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.Estado.CANCELADO)
        self.assertEqual(self.ejemplar_1.estado, Ejemplar.Estado.DISPONIBLE)
        self.assertIsNotNone(
            DetallePrestamo.objects.get(prestamo=prestamo).fecha_devolucion
        )
