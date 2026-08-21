import json
import os
import sys

from django.shortcuts import render, redirect

# solucion.py esta en la raiz del proyecto, junto a manage.py.
# Se agrega esa carpeta al path para poder importarlo sin reescribir
# la logica de decision (no se copia, se reutiliza).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from solucion import CATALOGO, decidir_venta, RUTA_DATOS  # noqa: E402


def resumen(request):
    """
    Pantalla unica de La Tiendita.

    - Si llega un POST (el vendedor envio el formulario), reutiliza
      decidir_venta() de la Fase 1, guarda el resultado en datos.json
      y vuelve a cargar la pagina (patron POST-Redirect-GET).
    - Siempre muestra el catalogo (producto, precio, stock) y la
      tabla de registros guardados en datos.json.
    - Si datos.json todavia no existe, no se cae: muestra la pagina
      vacia (sin registros).
    """
    if request.method == "POST":
        producto = request.POST.get("producto", "").strip()
        cantidad_texto = request.POST.get("cantidad", "").strip()

        try:
            cantidad = int(cantidad_texto)
        except ValueError:
            cantidad = -1

        resultado = decidir_venta(producto, cantidad, CATALOGO)

        registros = []
        if os.path.exists(RUTA_DATOS):
            with open(RUTA_DATOS) as f:
                registros = json.load(f)
        registros.append(resultado)
        with open(RUTA_DATOS, "w", encoding="utf-8") as f:
            json.dump(registros, f, indent=2, ensure_ascii=False)

        # Redirige para que un refresh de pagina no reenvie el formulario.
        return redirect("resumen")

    registros = []
    if os.path.exists(RUTA_DATOS):
        with open(RUTA_DATOS) as f:
            registros = json.load(f)

    catalogo_lista = [
        {"producto": nombre, "precio": datos["precio"], "stock": datos["stock"]}
        for nombre, datos in CATALOGO.items()
    ]

    return render(
        request,
        "resumen.html",
        {
            "registros": registros,
            "catalogo": catalogo_lista,
        },
    )
