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
Entra: un catalogo fijo de productos de La Tiendita (nombre, precio,
stock), una pantalla que registra ventas y muestra el catalogo y el
historial de ventas del dia. No entra: cuentas de usuario, cobro real
(pago electronico), edicion o eliminacion de registros ya guardados,
ni reportes por fecha.

**Priorizacion MoSCoW**

- **Must**
  - Pedir producto y cantidad al vendedor.
  - Decidir si la venta se acepta o se rechaza (y por que motivo).
  - Descontar el stock y calcular el total cuando se acepta.
  - Guardar cada registro en `datos.json`.
  - Mostrar el catalogo y el historial de ventas en una tabla (consola
    con `tabulate` y despues en la pagina web).
- **Should**
  - Poder corregir un registro mal ingresado (por ejemplo, si el
    vendedor se equivoco de cantidad).
  - Buscar/filtrar el historial por nombre de producto.
- **Could**
  - Exportar el resumen del dia a Excel.
  - Alertar cuando un producto queda con poco stock.
- **Won't** (en esta version)
  - Cuentas de usuario con contraseña por vendedor.
  - Cobro con tarjeta o integracion de pago.
  - Base de datos (se usa JSON; las bases de datos se ven en la Unidad 2).

## 2) Tecnico

**Datos de entrada**
- `producto` (texto): nombre del producto que se esta vendiendo.
- `cantidad` (numero entero): cuantas unidades se venden.

**Catalogo**
Diccionario en Python (`CATALOGO`, dentro de `solucion.py`) con los
productos reales de La Tiendita, su precio y un stock inicial de
prueba (la tienda no llevaba stock registrado antes de este proyecto,
asi que se definieron cantidades iniciales razonables para poder
probar el sistema).

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

**Paquete externo**
`tabulate`, para mostrar el catalogo y el historial de ventas como
tabla ordenada en la consola (Fase 2). Se instala con `pip install
tabulate` y se usa en `solucion.py` sobre la lista de registros leida
de `datos.json`.

**Pantalla web**
Una sola direccion (`/`, vista `resumen` en `core/views.py`):
- Con `GET` muestra un formulario para registrar una venta, la tabla
  del catalogo (producto, precio, stock) y la tabla de registros
  guardados en `datos.json`.
- Con `POST` reutiliza `decidir_venta()` de `solucion.py` (no la
  vuelve a escribir), guarda el nuevo registro en `datos.json` y
  redirige de vuelta a `/` para mostrar la tabla actualizada.
- Si `datos.json` todavia no existe, la pagina igual carga y muestra
  el historial vacio.
