import json
import sys
from datetime import date
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import ExtractWeekDay
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.base import TemplateView

from .forms import FormaPagoFormSet, ProductoForm, VentaItemFormSet
from .models import Compra, FormaPago, Producto, Venta

# solucion.py vive en la raiz del proyecto (junto a manage.py), fuera de core/,
# asi que se agrega esa carpeta al path para importar decidir_venta sin copiarla.
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from solucion import decidir_venta  # noqa: E402


def es_administrador(user):
    return user.is_superuser or user.groups.filter(name="Administrador").exists()


class GestionInventarioMixin(LoginRequiredMixin):
    """Permite a cualquier usuario autenticado administrar el inventario."""


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ventas = Venta.objects.all()
        compras = Compra.objects.all()
        ventas_aceptadas = ventas.filter(estado=Venta.Estado.ACEPTADA)
        ventas_por_dia = (
            ventas_aceptadas.annotate(dia_semana=ExtractWeekDay("creada_en"))
            .values("dia_semana")
            .annotate(unidades_vendidas=Sum("cantidad"))
            .order_by("-unidades_vendidas", "dia_semana")
        )
        productos_mas_vendidos = (
            ventas_aceptadas.values("producto__nombre")
            .annotate(unidades_vendidas=Sum("cantidad"))
            .order_by("-unidades_vendidas", "producto__nombre")
        )
        dias_semana = {
            1: "Domingo", 2: "Lunes", 3: "Martes", 4: "Miércoles",
            5: "Jueves", 6: "Viernes", 7: "Sábado",
        }
        dia_mas_ventas = ventas_por_dia.first()
        producto_mas_vendido = productos_mas_vendidos.first()

        total_vendido = ventas_aceptadas.aggregate(total=Sum("total"))["total"] or 0
        productos_stock_bajo = Producto.objects.filter(activo=True, stock__lte=5).order_by("stock")
        context.update({
            "total_productos": Producto.objects.filter(activo=True).count(),
            "stock_bajo": productos_stock_bajo.count(),
            "productos_stock_bajo": productos_stock_bajo,
            "ventas_hoy": compras.filter(creada_en__date=date.today()).count(),
            "ingresos": total_vendido,
            "total_vendido": total_vendido,
            "dia_mas_ventas": dias_semana.get(dia_mas_ventas["dia_semana"]) if dia_mas_ventas else None,
            "unidades_dia_mas_ventas": dia_mas_ventas["unidades_vendidas"] if dia_mas_ventas else 0,
            "producto_mas_vendido": producto_mas_vendido["producto__nombre"] if producto_mas_vendido else None,
            "unidades_producto_mas_vendido": producto_mas_vendido["unidades_vendidas"] if producto_mas_vendido else 0,
            "ultimas_compras": compras.select_related("vendedor").prefetch_related(
                "ventas__producto", "formas_pago"
            )[:5],
        })
        return context


class ProductoListView(GestionInventarioMixin, ListView):
    model = Producto
    template_name = "inventario/lista.html"
    context_object_name = "productos"


class ProductoCreateView(GestionInventarioMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/formulario.html"
    success_url = reverse_lazy("inventario:lista")

    def form_valid(self, form):
        messages.success(self.request, "Producto creado correctamente.")
        return super().form_valid(form)


class ProductoUpdateView(GestionInventarioMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/formulario.html"
    success_url = reverse_lazy("inventario:lista")

    def form_valid(self, form):
        messages.success(self.request, "Producto actualizado correctamente.")
        return super().form_valid(form)


@login_required
def producto_cambiar_estado(request, pk):
    if not es_administrador(request.user):
        messages.error(request, "Solo un administrador puede gestionar el catálogo de productos.")
        return redirect("dashboard")
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        producto.activo = not producto.activo
        producto.save(update_fields=["activo"])
        accion = "activado" if producto.activo else "retirado del catálogo"
        messages.success(request, f"Producto {accion} correctamente.")
        return redirect("inventario:lista")
    return render(request, "inventario/confirmar_cambio_estado.html", {"producto": producto})


def _productos_disponibles_json():
    productos = Producto.objects.filter(activo=True, stock__gt=0).order_by("nombre")
    datos = [
        {"id": p.pk, "nombre": p.nombre, "precio": p.precio, "codigo_barras": p.codigo_barras or ""}
        for p in productos
    ]
    # Evita que un nombre de producto con "</script>" corte el bloque <script> del template.
    return json.dumps(datos).replace("</", "<\\/")


@login_required
def registrar_venta(request):
    if request.method == "POST":
        formset = VentaItemFormSet(request.POST, prefix="form")
        pago_formset = FormaPagoFormSet(request.POST, prefix="pago")
        if formset.is_valid() and pago_formset.is_valid():
            items = [
                form.cleaned_data for form in formset
                if form.cleaned_data and not form.cleaned_data.get("DELETE")
            ]
            formas_pago = [
                form.cleaned_data for form in pago_formset
                if form.cleaned_data and not form.cleaned_data.get("DELETE")
            ]
            if not items:
                messages.error(request, "Agrega al menos un producto a la venta.")
            elif not formas_pago:
                messages.error(request, "Agrega al menos una forma de pago.")
            else:
                error = None
                with transaction.atomic():
                    compra = Compra.objects.create(vendedor=request.user)
                    total_a_pagar = 0
                    for item in items:
                        producto = Producto.objects.select_for_update().get(pk=item["producto"].pk)
                        cantidad = item["cantidad"]
                        catalogo_temp = {producto.nombre: {"precio": producto.precio, "stock": producto.stock}}
                        resultado = decidir_venta(producto.nombre, cantidad, catalogo_temp)
                        if resultado["estado"] != "Aceptado":
                            error = resultado["motivo"]
                            break
                        Venta.objects.create(
                            compra=compra, producto=producto, cantidad=cantidad, precio_unitario=producto.precio,
                            total=resultado["total"], estado=Venta.Estado.ACEPTADA, motivo=resultado["motivo"],
                            vendedor=request.user,
                        )
                        producto.stock = F("stock") - cantidad
                        producto.save(update_fields=["stock"])
                        total_a_pagar += resultado["total"]
                    if not error:
                        total_pagado = sum(fp["monto"] for fp in formas_pago)
                        if total_pagado < total_a_pagar:
                            error = (
                                f"El pago (${total_pagado}) no cubre el total a pagar (${total_a_pagar})."
                            )
                        else:
                            for fp in formas_pago:
                                FormaPago.objects.create(compra=compra, tipo=fp["tipo"], monto=fp["monto"])
                    if error:
                        transaction.set_rollback(True)
                if error:
                    messages.error(request, error)
                else:
                    messages.success(request, "Venta registrada y stock actualizado.")
                    return redirect("ventas:lista")
    else:
        formset = VentaItemFormSet(prefix="form")
        pago_formset = FormaPagoFormSet(prefix="pago")
    return render(request, "ventas/registrar.html", {
        "formset": formset,
        "pago_formset": pago_formset,
        "productos_json": _productos_disponibles_json(),
    })


class VentaListView(LoginRequiredMixin, ListView):
    model = Compra
    template_name = "ventas/lista.html"
    context_object_name = "compras"

    def get_queryset(self):
        return Compra.objects.select_related("vendedor").prefetch_related("ventas__producto", "formas_pago")
