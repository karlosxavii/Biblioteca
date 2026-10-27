from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class AutenticacionTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="admin123",
            nombre_completo="Administrador General",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.lector_user = Usuario.objects.create_user(
            username="lector",
            password="lector123",
            nombre_completo="Ana Torres",
            rol=Usuario.Rol.LECTOR,
        )

    def test_login_correcto_redirige_al_panel(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {"username": "admin", "password": "admin123"},
        )
        self.assertRedirects(response, reverse("core:dashboard"))

    def test_login_incorrecto_muestra_error(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {"username": "admin", "password": "incorrecta"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("__all__", response.context["form"].errors)

    def test_anonimo_redirigido_al_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('usuarios:login')}?next={reverse('core:dashboard')}",
        )

    def test_lector_no_accede_a_usuarios(self):
        self.client.force_login(self.lector_user)
        response = self.client.get(reverse("usuarios:list"))
        self.assertEqual(response.status_code, 403)

    def test_administrador_lista_usuarios(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("usuarios:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "lector")


class UsuarioCrudTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="admin123",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.admin)

    def test_crear_usuario_con_password_cifrada(self):
        response = self.client.post(
            reverse("usuarios:create"),
            {
                "username": "nuevo",
                "nombre_completo": "Nuevo Usuario",
                "email": "nuevo@example.com",
                "rol": Usuario.Rol.BIBLIOTECARIO,
                "is_active": "on",
                "password1": "ClaveSegura123",
                "password2": "ClaveSegura123",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        usuario = Usuario.objects.get(username="nuevo")
        self.assertTrue(usuario.check_password("ClaveSegura123"))
        self.assertEqual(usuario.rol, Usuario.Rol.BIBLIOTECARIO)

    def test_no_puede_desactivar_su_propio_usuario(self):
        response = self.client.post(
            reverse("usuarios:update", args=[self.admin.pk]),
            {
                "username": self.admin.username,
                "nombre_completo": self.admin.nombre_completo,
                "email": "",
                "rol": self.admin.rol,
                "password1": "",
                "password2": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No puedes desactivar tu propio usuario")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_toggle_estado_usuario(self):
        otro = Usuario.objects.create_user(
            username="biblio",
            password="clave123",
            rol=Usuario.Rol.BIBLIOTECARIO,
        )
        self.client.post(reverse("usuarios:toggle", args=[otro.pk]))
        otro.refresh_from_db()
        self.assertFalse(otro.is_active)
