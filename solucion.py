"""
La Tiendita - Fase 1 y 2
------------------------
Programa de consola para que un vendedor registre la venta de un producto
del almacen saludable "La Tiendita".

Decide si la venta se puede realizar segun dos datos:
 - el nombre del producto (¿existe en el catalogo?)
 - la cantidad pedida (¿hay stock suficiente?)

Resultados posibles (4):
 1) Dato invalido   -> la cantidad pedida es 0 o negativa
 2) Rechazo motivo A -> el producto no existe en el catalogo
 3) Rechazo motivo B -> el producto existe pero no hay stock suficiente
 4) Aceptado        -> se descuenta el stock y se calcula el total a pagar

Este archivo se usa de dos formas:
 - Ejecutado directo (python solucion.py): pide datos por consola,
   guarda el registro en datos.json y muestra la tabla con tabulate.
 - Importado desde Django (core/views.py): se reutiliza la funcion
   decidir_venta() y el CATALOGO, sin repetir la logica.
"""

import json
import os
from copy import deepcopy
from tabulate import tabulate

# Ruta de datos.json: siempre junto a este archivo (junto a manage.py)
RUTA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos.json")
RUTA_CATALOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogo.json")

# Catalogo de La Tiendita: nombre -> precio (CLP) y stock disponible.
# El stock inicial es un supuesto razonable para la version de prueba
# (no fue entregado por la tienda), y queda documentado en plan.md.
CATALOGO = {
    "Kombucha": {"precio": 2500, "stock": 20},
    "Electrolit": {"precio": 3000, "stock": 15},
    "Agua de coco 500ml": {"precio": 3000, "stock": 18},
    "Agua de coco 330ml": {"precio": 2500, "stock": 18},
    "Agua 1.5 litros": {"precio": 2000, "stock": 30},
    "Jugo bless": {"precio": 2500, "stock": 12},
    "Vitamin water": {"precio": 2100, "stock": 10},
    "Barritas gudfud": {"precio": 3000, "stock": 25},
    "Sal Rosada Manare": {"precio": 4290, "stock": 8},
    "Mantequilla de almendras": {"precio": 8990, "stock": 6},
    "Ghee manare": {"precio": 14990, "stock": 5},
    "Cereal manare": {"precio": 1000, "stock": 40},
    "Avena instantanea": {"precio": 5790, "stock": 14},
    "Aceite de coco": {"precio": 4990, "stock": 10},
    "Bandeja 30 huevos": {"precio": 12000, "stock": 9},
    "Extra life": {"precio": 2000, "stock": 16},
    "Arriendo mat": {"precio": 2500, "stock": 4},
    "Miel 1kg": {"precio": 12000, "stock": 7},
    "Keto crunch": {"precio": 4000, "stock": 11},
    "Premium mix": {"precio": 3500, "stock": 13},
    "Alfajor ketofree": {"precio": 3900, "stock": 20},
    "Volkis ketofree": {"precio": 3890, "stock": 20},
    "Galleton ketofree": {"precio": 2900, "stock": 22},
    "Moroketo ketofree": {"precio": 2790, "stock": 22},
    "Berrysur batido": {"precio": 3000, "stock": 17},
}


def cargar_catalogo():
    """Carga el catálogo editable o entrega una copia del catálogo inicial."""
    if os.path.exists(RUTA_CATALOGO):
        with open(RUTA_CATALOGO, "r", encoding="utf-8") as f:
            return json.load(f)
    return deepcopy(CATALOGO)


def guardar_catalogo(catalogo):
    """Guarda los cambios de productos, precios y stock."""
    with open(RUTA_CATALOGO, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)


def decidir_venta(producto, cantidad, catalogo):
    """
    Regla de decision de La Tiendita.

    Recibe el nombre del producto (texto), la cantidad pedida (entero)
    y el catalogo (dict). No modifica el catalogo recibido: devuelve
    una copia actualizada solo cuando la venta es aceptada.

    Devuelve un diccionario con: estado, motivo y total (si aplica).
    El orden de las condiciones importa: primero se revisa el dato
    invalido, porque si se dejara al final nunca se alcanzaria a revisar.
    """
    if cantidad <= 0:
        return {
            "producto": producto,
            "cantidad": cantidad,
            "estado": "Dato invalido",
            "motivo": "La cantidad debe ser mayor a cero",
            "total": 0,
        }

    elif producto not in catalogo:
        return {
            "producto": producto,
            "cantidad": cantidad,
            "estado": "Rechazado",
            "motivo": "El producto no existe en el catalogo",
            "total": 0,
        }

    elif cantidad > catalogo[producto]["stock"]:
        return {
            "producto": producto,
            "cantidad": cantidad,
            "estado": "Rechazado",
            "motivo": f"Stock insuficiente (quedan {catalogo[producto]['stock']})",
            "total": 0,
        }

    else:
        precio = catalogo[producto]["precio"]
        total = precio * cantidad
        catalogo[producto]["stock"] -= cantidad
        return {
            "producto": producto,
            "cantidad": cantidad,
            "estado": "Aceptado",
            "motivo": f"Venta realizada, quedan {catalogo[producto]['stock']} en stock",
            "total": total,
        }


def cargar_registros():
    """Lee datos.json si existe. Si no existe, empieza con una lista vacia."""
    if os.path.exists(RUTA_DATOS):
        with open(RUTA_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_registros(registros):
    """Escribe la lista completa de registros en datos.json."""
    with open(RUTA_DATOS, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=2, ensure_ascii=False)


def main():
    print("=== La Tiendita - Registro de venta ===")
    producto = input("Nombre del producto: ").strip()
    cantidad_texto = input("Cantidad: ").strip()

    # input() siempre entrega texto: si no se puede convertir a numero,
    # se trata igual como dato invalido (cantidad = -1 fuerza ese resultado).
    try:
        cantidad = int(cantidad_texto)
    except ValueError:
        cantidad = -1

    catalogo = cargar_catalogo()
    resultado = decidir_venta(producto, cantidad, catalogo)
    if resultado["estado"] == "Aceptado":
        guardar_catalogo(catalogo)

    print(f"\nResultado: {resultado['estado']}")
    print(f"Motivo: {resultado['motivo']}")
    if resultado["estado"] == "Aceptado":
        print(f"Total a pagar: ${resultado['total']}")

    registros = cargar_registros()
    registros.append(resultado)
    guardar_registros(registros)

    print("\n=== Registros guardados en datos.json ===")
    print(tabulate(registros, headers="keys"))


if __name__ == "__main__":
    main()
