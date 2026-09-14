# Plan · La Tiendita

## 1) Negocio

**Problema**
La Tiendita es un almacen de alimentacion saludable que esta partiendo y
le va bien, pero funciona "a la antigua": no tiene ningun sistema
informatico. El vendedor no tiene forma de saber, en el momento en que
alguien compra, si queda stock suficiente de un producto ni cuanto hay
que cobrar. Las ventas y el stock se llevan de memoria, lo que hace
facil vender algo que ya no queda o cobrar mal.

**Solucion**
Una pagina web donde el vendedor escribe el producto y la cantidad que
se esta vendiendo. El sistema revisa el catalogo, decide si la venta se
puede hacer, descuenta el stock, calcula el total a cobrar y deja el
registro guardado para no perder el historial del dia.

**Alcance**
Entra: catalogo de productos de La Tiendita (nombre, codigo de barras,
precio, stock) administrado en base de datos; login con cuentas de
usuario y dos roles (Administrador y Vendedor); una pantalla que
registra ventas (una o varias lineas de producto por compra) y un
dashboard que muestra el catalogo, el historial de compras y
estadisticas basicas. No entra: cobro real (pago electronico), edicion
o eliminacion de compras ya registradas, ni reportes por fecha.

La Tiendita es un almacen familiar: Administrador y Vendedor son ambos
dueños del negocio, asi que comparten los permisos de gestion normal
del catalogo (crear y editar productos) y de venta. Solo
retirar/reactivar un producto del catalogo queda exclusivo del
Administrador, por ser una accion mas sensible (saca o repone algo del
catalogo activo, no solo ajusta un dato).

**Priorizacion MoSCoW**

- **Must**
  - Pedir producto y cantidad al vendedor.
  - Decidir si la venta se acepta o se rechaza (y por que motivo).
  - Descontar el stock y calcular el total cuando se acepta.
  - Guardar cada registro en base de datos (SQLite).
  - Mostrar el catalogo y el historial de ventas en una tabla (consola
    con `tabulate` para la version de archivo, y en la pagina web para
    la version con base de datos).
  - Login con cuentas de usuario y roles (Administrador y Vendedor):
    ambos roles pueden crear/editar productos y registrar ventas;
    solo un Administrador puede retirar o reactivar un producto del
    catalogo.
- **Should**
  - Poder corregir un registro mal ingresado (por ejemplo, si el
    vendedor se equivoco de cantidad).
  - Buscar/filtrar el historial por nombre de producto.
- **Could**
  - Exportar el resumen del dia a Excel.
  - Alertar cuando un producto queda con poco stock.
- **Won't** (en esta version)
  - Cobro con tarjeta o integracion de pago.

## 2) Tecnico

**Datos de entrada**
- `producto` (texto): nombre del producto que se esta vendiendo.
- `cantidad` (numero entero): cuantas unidades se venden.

**Catalogo**
El diccionario `CATALOGO` en `solucion.py` sigue existiendo para la
version de consola (Fase 1/2, sin base de datos). Para la version web
(Eva2) el catalogo vive en SQLite, en el modelo `Producto`.

**Modelo de datos (SQLite, `core/models.py`)**
- `Producto`: nombre, codigo de barras (opcional, unico), precio,
  stock, y si esta activo (los productos retirados se desactivan, no
  se borran, para no perder el historial de ventas asociado).
- `Compra`: una transaccion de venta — vendedor, metodo de pago
  (debito, credito, efectivo, transferencia) y fecha. Agrupa una o
  varias lineas de producto para poder vender varios productos en una
  sola compra.
- `Venta`: una linea dentro de una `Compra` — el producto, la
  cantidad, el precio unitario, el total y el resultado de la regla de
  decision (estado y motivo).

**Roles y permisos**
Dos grupos de Django: `Administrador` y `Vendedor` (creados por
migracion). Cualquier usuario autenticado puede registrar ventas, ver
el dashboard, y crear o editar productos del catalogo (ambos roles son
dueños del negocio y comparten esa gestion normal). Retirar o
reactivar un producto (`producto_cambiar_estado`) es la unica accion
restringida al grupo `Administrador` (o superusuario), por ser mas
sensible; la restriccion se aplica en la vista del servidor
(`core/views.py`), no solo ocultando un boton en el template.

**Regla de decision (4 resultados)**
1. **Dato invalido**: `cantidad <= 0` (o el texto ingresado no es un
   numero) → "La cantidad debe ser mayor a cero".
2. **Rechazado (motivo A)**: el producto no existe en el catalogo →
   "El producto no existe en el catalogo".
3. **Rechazado (motivo B)**: el producto existe pero `cantidad` es
   mayor al stock disponible → "Stock insuficiente".
4. **Aceptado**: el producto existe y hay stock suficiente → se
   descuenta el stock, se calcula `total = precio * cantidad` y se
   guarda el registro.

El orden de las condiciones revisa primero el dato invalido, porque si
se revisara al final nunca se alcanzaria a evaluar.

En la version web, `core/views.py` importa `decidir_venta()` desde
`solucion.py` (agregando la raiz del proyecto al `sys.path`, ya que
`solucion.py` esta fuera de `core/`) y la llama una vez por cada linea
de producto de la compra, con un catalogo temporal de un solo producto
armado a partir del `Producto` de la base de datos. La regla no se
reescribe ni se copia: vive en un solo lugar.

**Paquete externo**
`tabulate`, para mostrar el catalogo y el historial de ventas como
tabla ordenada en la consola (Fase 2). Se instala con `pip install
tabulate` y se usa en `solucion.py` sobre la lista de registros leida
de `datos.json`.

**Pantalla web**
Varias direcciones, con login obligatorio (`/`, vista de login):
- `/dashboard/`: resumen con productos activos, stock bajo, ventas del
  dia, ingresos y un analisis estadistico de las ventas aceptadas.
- `/ventas/nueva/`: formulario para registrar una compra con una o
  varias lineas de producto (por seleccion o por codigo de barras) y
  un metodo de pago; usa `decidir_venta()` para cada linea y descuenta
  el stock solo si toda la compra se puede aceptar.
- `/ventas/`: historial de compras registradas.
- `/inventario/productos/` y sus vistas de crear/editar: CRUD del
  catalogo, abierto a cualquier usuario autenticado. Cambiar estado
  (retirar/reactivar) esta restringido al grupo Administrador.
