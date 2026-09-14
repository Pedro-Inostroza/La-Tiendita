# ia.md · Uso de IA en este proyecto

**Herramienta usada:** Claude (chat de Anthropic), para ordenar el
plan de negocio/tecnico y para revisar la estructura del proyecto
Django antes de programarlo a mano.

**Consulta concreta**
Le pedi lo siguiente, siguiendo el formato sugerido en las
instrucciones de la evaluacion:

> "Soy estudiante de programacion back end. Quiero
> resolver este problema: un almacen de alimentacion saludable
> llamado La Tiendita no tiene sistema para registrar ventas ni
> stock, y el vendedor no sabe si queda stock cuando alguien compra.
> Ayudame a escribir un plan de 2 planas con apartado de negocio
> (problema, solucion, alcance, MoSCoW) y apartado tecnico (datos de
> entrada, regla de decision con 4 resultados, paquete externo,
> pantalla web). Restriccion: se resuelve con variables, if/elif, un
> archivo JSON y una sola vista Django. Sin base de datos, sin login,
> sin API."

La IA devolvio una propuesta de plan con la estructura de negocio y
tecnico pedida, un catalogo de ejemplo, y una version inicial de la
regla de decision.

**Que estaba mal, sobraba o no entendi, y como lo corregi**

- La primera version que propuso la IA solo tenia **3 resultados**
  (aceptado, rechazado por stock, y un caso por defecto). Le faltaba
  el resultado de "producto no existe en el catalogo" como motivo de
  rechazo distinto al de stock insuficiente. Lo note al revisar la
  regla contra la exigencia de la pauta (4 resultados: aceptacion,
  dos rechazos por motivos distintos, dato invalido) y agregue yo el
  `elif` que falta en `solucion.py`.
- La IA sugirio en un momento guardar los datos con **SQLite**
  "porque es mas ordenado". Esto no corresponde a esta version del
  proyecto (que usa JSON, sin base de datos, segun las instrucciones),
  asi que descarte esa parte y me quede con `json.dump()` /
  `json.load()`.
- Tambien propuso poner la `SECRET_KEY` directamente escrita en
  `settings.py` en el ejemplo de Django. La cambie para leerla desde
  `.env` con `python-decouple`, dejando `.env` fuera del repositorio
  (en `.gitignore`) y subiendo solo `.env.example`, tal como se pide
  en las instrucciones.
- Revise a mano el `import` de `solucion.py` dentro de `core/views.py`:
  la version que sugirio la IA reescribia la logica de decision
  directamente en la vista, duplicando el codigo. La corregi para que
  la vista solo importe `decidir_venta()` y `CATALOGO` desde
  `solucion.py`, y asi la logica vive en un solo lugar, como pide el
  bloque 11 de las instrucciones.

En resumen: la IA ayudo a ordenar la estructura del plan y a partir de
un catalogo de ejemplo, pero la regla de decision completa, la
separacion entre `solucion.py` y la vista, y el manejo de la clave
secreta los revise y corregi yo antes de dar por terminada cada fase.

## Eva2 — migracion a Django con base de datos y roles

**Herramienta usada:** Claude Code (Anthropic), para migrar el
proyecto de ES1 (JSON, sin login) a esta version con modelos en
SQLite, autenticacion y roles.

**Consulta concreta**
Le pedi que agregara permisos por rol a las vistas de inventario:

> "Decisión de negocio: solo el grupo 'Administrador' (o un
> superusuario) puede crear, editar, o cambiar el estado
> (activar/desactivar) de productos. Cualquier usuario autenticado
> puede registrar ventas y ver el dashboard/listado de ventas.
> Corrígelo así: crea un mixin que verifique el grupo del usuario y
> aplícalo a las vistas de creación, edición y cambio de estado. Si un
> usuario sin permiso intenta acceder, debe redirigir con un mensaje
> de error, no un error 500 ni una página en blanco."

**Que estaba mal, sobraba o no entendi, y como lo corregi**

Antes de este pedido, `GestionInventarioMixin` (el mixin que protegia
las vistas de crear/editar/cambiar estado de productos) solo heredaba
de `LoginRequiredMixin`. Eso significa que **cualquier** usuario
autenticado —del grupo Vendedor o Administrador— podia crear, editar o
retirar productos del catalogo con solo escribir la URL, aunque el
boton correspondiente estuviera oculto en el template con
`{% if es_admin %}`. Es exactamente el error que advierte la pauta:
esconder un boton en el HTML no es una restriccion real, porque el
usuario puede saltarsela llamando la URL directo (por ejemplo con un
POST manual). Tuve que:

- Crear un `UserPassesTestMixin` propio (`SoloAdministradorMixin`) que
  revisa `request.user.is_superuser or
  request.user.groups.filter(name="Administrador").exists()` en el
  servidor, no en la plantilla.
- Aplicarlo a `ProductoCreateView`, `ProductoUpdateView` y a la vista
  `producto_cambiar_estado`, dejando el dashboard y el registro de
  ventas abiertos a cualquier usuario autenticado (eso si debe ser
  compartido entre roles).
- Agregar un test que hace `POST` directo a `inventario:crear` e
  `inventario:editar` con un usuario del grupo Vendedor y confirma que
  lo rechaza (redirect, sin cambios en la base de datos), en vez de
  solo revisar que el boton no aparezca en el HTML.

En resumen: la parte de permisos no se resolvio dejando que la interfaz
ocultara opciones, sino agregando la verificacion de rol en cada vista
del servidor, y probando el rechazo con un request real en vez de
confiar en que el HTML se viera bien.

## Ajuste final de roles - conversacion con el profesor

Despues de la primera version (que restringia crear, editar Y retirar
productos solo a Administrador), hable con el profesor sobre el
contexto real del negocio: La Tiendita es un almacen familiar donde
el Administrador y el Vendedor son ambos duenos (pareja). El profesor
confirmo que en ese contexto tiene sentido que compartan la mayoria
de los permisos operativos.

Ajuste el diseno para que:
- Crear y editar productos, y registrar ventas: compartido entre
  Administrador y Vendedor (sin restriccion de rol).
- Retirar o reactivar un producto del catalogo: exclusivo del
  Administrador, por ser una accion mas sensible sobre el inventario.

Esto no fue una correccion a la IA, sino un ajuste de alcance despues
de validar el diseno con el profesor. Actualice el mixin
GestionInventarioMixin (vuelve a ser solo LoginRequiredMixin) y deje
la verificacion de rol unicamente en producto_cambiar_estado. Tambien
actualice los tests: uno confirma que un Vendedor SI puede crear/
editar, y otro confirma que NO puede retirar un producto.