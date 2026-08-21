# ia.md · Uso de IA en este proyecto

**Herramienta usada:** Claude (chat de Anthropic), para ordenar el
plan de negocio/tecnico y para revisar la estructura del proyecto
Django antes de programarlo a mano.

**Consulta concreta**
Le pedi lo siguiente, siguiendo el formato sugerido en las
instrucciones de la evaluacion:

> "Soy estudiante de programacion back end, primer semestre. Quiero
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
