# La Tiendita - Sistema de ventas para almacén saludable

Proyecto Django (Evaluación 2) para gestionar el inventario y las ventas de un
almacén saludable: catálogo de productos, registro de ventas con lector de
código de barras, múltiples formas de pago por compra y un panel con análisis
estadístico.

## Requisitos

- Python 3.12 o superior
- pip

## Instalación

1. Clonar el repositorio y entrar en la rama `eva2`:

   ```
   git clone https://github.com/Pedro-Inostroza/La-Tiendita.git
   cd La-Tiendita
   git checkout eva2
   ```

2. Instalar dependencias:

   ```
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:

   ```
   cp .env.example .env
   ```

   Luego edita `.env` y define un `SECRET_KEY` propio. `DEBUG=true` sirve para
   desarrollo; con `DEBUG=false` la app queda lista para revisión.

4. Aplicar migraciones:

   ```
   python manage.py migrate
   ```

5. Crear un superusuario (administrador):

   ```
   python manage.py createsuperuser
   ```

   Luego, desde el panel `/admin/`, agrega ese usuario al grupo
   **Administrador** para que tenga permisos completos. Los usuarios del grupo
   **Vendedor** pueden vender y editar stock/precio, pero no retirar productos.

6. Correr el servidor:

   ```
   python manage.py runserver
   ```

## Acceso

- Administrador web: http://127.0.0.1:8000/admin/
- Sistema de ventas: http://127.0.0.1:8000/

## Estructura

- `core/` — aplicación principal (modelos, vistas, formularios, plantillas).
- `solucion.py` — lógica de decisión de la ES1 (`decidir_venta`), en la raíz del
  proyecto junto a `manage.py`. `core/views.py` la importa tal cual, sin
  duplicar el código, agregando la raíz del proyecto al `sys.path`.
- `miproyecto/` — configuración del proyecto Django.

## Nota sobre datos

El catálogo inicial (`Producto`) se siembra automáticamente en la migración
`0002_roles_y_catalogo_inicial.py`, en vez de importar desde `datos.json` de la
ES1. Esto permite que cualquiera pueda clonar y ejecutar el proyecto sin
archivos adicionales. Esa misma migración crea los grupos **Administrador** y
**Vendedor** con sus permisos.

## Tests

```
python manage.py check
python manage.py test
```
