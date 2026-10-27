from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalogo.models import Autor, Ejemplar, Libro
from lectores.models import Lector
from prestamos.models import Prestamo
from prestamos.services import crear_prestamo, devolver_ejemplar
from usuarios.models import Usuario

AUTORES = [
    ("Gabriel", "García Márquez", "Colombiana", 1927),
    ("Isabel", "Allende", "Chilena", 1942),
    ("Jorge Luis", "Borges", "Argentina", 1899),
    ("Mario", "Vargas Llosa", "Peruana", 1936),
    ("Julio", "Cortázar", "Argentina", 1914),
]

LIBROS = [
    ("Cien años de soledad", "978-0307474728", "Sudamericana", 1967, "Novela", 0),
    ("La casa de los espíritus", "978-0525433477", "Plaza & Janés", 1982, "Novela", 1),
    ("Ficciones", "978-0802130303", "Sur", 1944, "Cuento", 2),
    ("La ciudad y los perros", "978-8420471839", "Seix Barral", 1963, "Novela", 3),
    ("Rayuela", "978-8437604572", "Sudamericana", 1963, "Novela", 4),
]


class Command(BaseCommand):
    help = "Crea usuarios, catálogo y préstamos de demostración."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina los datos de demostración antes de recrearlos.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Prestamo.objects.all().delete()
            Ejemplar.objects.all().delete()
            Libro.objects.all().delete()
            Autor.objects.all().delete()
            Lector.objects.all().delete()
            Usuario.objects.filter(
                username__in=["admin", "bibliotecario", "lector"]
            ).delete()

        admin = self._usuario(
            "admin",
            "Administrador General",
            "ADMINISTRADOR",
            "admin123",
            is_staff=True,
            is_superuser=True,
        )
        bibliotecario = self._usuario(
            "bibliotecario",
            "Laura Bibliotecaria",
            "BIBLIOTECARIO",
            "biblio123",
        )
        usuario_lector = self._usuario(
            "lector",
            "Ana Torres",
            "LECTOR",
            "lector123",
        )

        autores = []
        for nombres, apellidos, nacionalidad, nacimiento in AUTORES:
            autor, _ = Autor.objects.get_or_create(
                nombres=nombres,
                apellidos=apellidos,
                defaults={
                    "nacionalidad": nacionalidad,
                    "fecha_nacimiento": date(nacimiento, 1, 1),
                },
            )
            autores.append(autor)

        libros = []
        for titulo, isbn, editorial, anio, genero, indice_autor in LIBROS:
            libro, creado = Libro.objects.get_or_create(
                isbn=isbn,
                defaults={
                    "titulo": titulo,
                    "editorial": editorial,
                    "anio_publicacion": anio,
                    "genero": genero,
                    "sinopsis": f"Obra de demostración: {titulo}.",
                },
            )
            if creado:
                libro.autores.add(autores[indice_autor])
            libros.append(libro)

        for indice, libro in enumerate(libros, start=1):
            for copia in range(1, 3):
                codigo = f"EJ-{indice:02d}{copia:02d}"
                Ejemplar.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        "libro": libro,
                        "ubicacion": f"Estante {chr(64 + indice)}",
                    },
                )

        lector, _ = Lector.objects.get_or_create(
            documento="1020304050",
            defaults={
                "nombres": "Ana",
                "apellidos": "Torres",
                "email": "ana.torres@example.com",
                "telefono": "3001234567",
                "direccion": "Calle 10 # 20-30",
                "usuario": usuario_lector,
            },
        )
        if lector.usuario_id is None:
            lector.usuario = usuario_lector
            lector.save(update_fields=["usuario"])

        Lector.objects.get_or_create(
            documento="99887766",
            defaults={
                "nombres": "Carlos",
                "apellidos": "Ruiz",
                "email": "carlos.ruiz@example.com",
                "telefono": "3109876543",
            },
        )

        if not Prestamo.objects.exists():
            hoy = timezone.localdate()
            primer_ejemplar = libros[0].ejemplares.filter(estado=Ejemplar.Estado.DISPONIBLE).first()
            if primer_ejemplar:
                crear_prestamo(
                    lector=lector,
                    bibliotecario=bibliotecario,
                    fecha_prestamo=hoy - timedelta(days=2),
                    fecha_entrega=hoy + timedelta(days=5),
                    ejemplares=[primer_ejemplar],
                    observaciones="Préstamo de demostración activo.",
                )

            segundo_ejemplar = libros[1].ejemplares.filter(estado=Ejemplar.Estado.DISPONIBLE).first()
            if segundo_ejemplar:
                prestamo = crear_prestamo(
                    lector=lector,
                    bibliotecario=bibliotecario,
                    fecha_prestamo=hoy - timedelta(days=20),
                    fecha_entrega=hoy - timedelta(days=13),
                    ejemplares=[segundo_ejemplar],
                    observaciones="Préstamo de demostración ya devuelto.",
                )
                devolver_ejemplar(
                    prestamo.detalles.first(),
                    fecha=hoy - timedelta(days=15),
                )

        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))
        self.stdout.write("  admin / admin123")
        self.stdout.write("  bibliotecario / biblio123")
        self.stdout.write("  lector / lector123")

    def _usuario(self, username, nombre, rol, password, **extra):
        usuario, creado = Usuario.objects.get_or_create(
            username=username,
            defaults={
                "nombre_completo": nombre,
                "rol": rol,
                "email": f"{username}@biblioteca.local",
                **extra,
            },
        )
        if creado:
            usuario.set_password(password)
            usuario.save()
        return usuario
