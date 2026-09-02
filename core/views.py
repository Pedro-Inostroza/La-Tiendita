from datetime import date

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

from .forms import ProductoForm, VentaForm
from .models import Producto, Venta


class GestionInventarioMixin(LoginRequiredMixin):
    """Permite a cualquier usuario autenticado administrar el inventario."""


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ventas = Venta.objects.all()
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
        context.update({
            "total_productos": Producto.objects.filter(activo=True).count(),
            "stock_bajo": Producto.objects.filter(activo=True, stock__lte=5).count(),
            "ventas_hoy": ventas.filter(creada_en__date=date.today()).count(),
            "ingresos": total_vendido,
            "total_vendido": total_vendido,
            "dia_mas_ventas": dias_semana.get(dia_mas_ventas["dia_semana"]) if dia_mas_ventas else None,
            "unidades_dia_mas_ventas": dia_mas_ventas["unidades_vendidas"] if dia_mas_ventas else 0,
            "producto_mas_vendido": producto_mas_vendido["producto__nombre"] if producto_mas_vendido else None,
            "unidades_producto_mas_vendido": producto_mas_vendido["unidades_vendidas"] if producto_mas_vendido else 0,
            "ultimas_ventas": ventas.select_related("producto", "vendedor")[:5],
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
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        producto.activo = not producto.activo
        producto.save(update_fields=["activo"])
        accion = "activado" if producto.activo else "retirado del catálogo"
        messages.success(request, f"Producto {accion} correctamente.")
        return redirect("inventario:lista")
    return render(request, "inventario/confirmar_cambio_estado.html", {"producto": producto})


@login_required
def registrar_venta(request):
    if request.method == "POST":
        form = VentaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                producto = Producto.objects.select_for_update().get(pk=form.cleaned_data["producto"].pk)
                cantidad = form.cleaned_data["cantidad"]
                if cantidad > producto.stock:
                    form.add_error("cantidad", f"Stock insuficiente. Solo hay {producto.stock} unidades disponibles.")
                else:
                    total = producto.precio * cantidad
                    Venta.objects.create(
                        producto=producto, cantidad=cantidad, precio_unitario=producto.precio,
                        total=total, estado=Venta.Estado.ACEPTADA, motivo="Venta registrada", vendedor=request.user,
                    )
                    producto.stock = F("stock") - cantidad
                    producto.save(update_fields=["stock"])
                    messages.success(request, "Venta registrada y stock actualizado.")
                    return redirect("ventas:lista")
    else:
        form = VentaForm()
    return render(request, "ventas/registrar.html", {"form": form})


class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = "ventas/lista.html"
    context_object_name = "ventas"

    def get_queryset(self):
        return Venta.objects.select_related("producto", "vendedor")
