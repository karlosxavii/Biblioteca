# Biblioteca Central

Sistema de gestión de biblioteca para registrar libros, autores, ejemplares físicos, lectores y préstamos con fechas de entrega y devolución.

Proyecto desarrollado con **Django 6.1.2** y **SQLite**.

## Funcionalidades

- Catálogo de libros con relación muchos-a-muchos con autores.
- Ejemplares físicos por libro (relación uno-a-muchos).
- Lectores con ficha propia y vinculación opcional a un usuario de acceso.
- Préstamos con múltiples ejemplares mediante `DetallePrestamo`.
- Devolución individual de cada ejemplar y cierre automático del préstamo.
- Control de disponibilidad: un ejemplar prestado no puede prestarse dos veces.
- Detección de préstamos vencidos y límite de 5 préstamos activos por lector.
- Panel con indicadores, préstamos recientes, vencidos y próximas entregas.
- Búsqueda y filtros en todos los listados, con paginación.
- Roles diferenciados: administrador, bibliotecario y lector.
- Administración de Django disponible en `/admin/`.

## Modelo de datos

```text
Usuario (roles: Administrador, Bibliotecario, Lector)
Autor  N:M  Libro
Libro  1:N  Ejemplar          (entidad débil)
Lector 1:N  Prestamo
Prestamo 1:N DetallePrestamo
Ejemplar 1:N DetallePrestamo
DetallePrestamo: fecha_devolucion
```

Relaciones clave implementadas:

- `Libro` 1:N `Ejemplar` mediante `Ejemplar.libro` con borrado en cascada.
- `Lector` 1:N `Prestamo` mediante `Prestamo.lector`.
- `Prestamo` N:M `Ejemplar` mediante `DetallePrestamo`, con `fecha_devolucion` por ejemplar.
- `Libro` N:M `Autor` mediante `Libro.autores`.

## Roles y permisos

| Rol | Permisos |
| --- | --- |
| Administrador | Todo el sistema, usuarios y Django admin. |
| Bibliotecario | Catálogo, lectores, préstamos y devoluciones. |
| Lector | Consulta del catálogo y sus propios préstamos. |

## Estructura

```text
manage.py
biblioteca/          Configuración del proyecto (settings, urls, wsgi)
core/                Panel, búsqueda, mixins y utilidades de plantillas
usuarios/            Usuario personalizado y administración de accesos
catalogo/            Autor, Libro y Ejemplar
lectores/            Lector
prestamos/           Prestamo, DetallePrestamo y servicios de circulación
templates/           Plantillas Django
static/              CSS y JavaScript
```

## Instalación

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abrir `http://127.0.0.1:8000`.

Credenciales de demostración:

- Administrador: `admin / admin123`
- Bibliotecario: `bibliotecario / biblio123`
- Lector: `lector / lector123`

Para crear un administrador propio:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

## Comandos útiles

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo --reset
.\.venv\Scripts\python.exe manage.py test
```

## Configuración

Las variables se leen desde `.env`:

```env
SECRET_KEY=cambia-esta-clave-en-produccion
DEBUG=true
ALLOWED_HOSTS=127.0.0.1,localhost
APP_NAME=Biblioteca Central
TIME_ZONE=America/Bogota
ITEMS_PER_PAGE=15
```

La base de datos se guarda en `db.sqlite3`. Para usar otra base solo se debe cambiar `DATABASES` en `biblioteca/settings.py`.

## Flujo de préstamo

1. Se registra un libro y sus autores.
2. Se agregan uno o más ejemplares al libro.
3. Se registra el lector (opcionalmente con usuario de acceso).
4. El bibliotecario crea el préstamo, selecciona los ejemplares disponibles y define la fecha de entrega.
5. Cada ejemplar pasa a estado `PRESTADO`.
6. Al registrar la devolución, el ejemplar vuelve a `DISPONIBLE`.
7. Cuando todos los ejemplares del préstamo se devuelven, el préstamo pasa a `DEVUELTO`.

## Pruebas

```powershell
.\.venv\Scripts\python.exe manage.py test -v 2
```

Las pruebas cubren autenticación, permisos por rol, CRUD de catálogo, préstamos, devoluciones, cancelaciones, vencimientos y navegación de las páginas principales.
