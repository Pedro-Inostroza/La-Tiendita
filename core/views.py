from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.base import TemplateView

from .forms import ProductoForm, VentaForm
from .models import Producto, Venta


def es_administrador(user):
    return user.is_superuser or user.groups.filter(name="Administrador").exists()


class SoloAdministradorMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return es_administrador(self.request.user)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ventas = Venta.objects.all() if es_administrador(self.request.user) else Venta.objects.filter(vendedor=self.request.user)
        context.update({
            "total_productos": Producto.objects.count(),
            "stock_bajo": Producto.objects.filter(stock__lte=5).count(),
            "ventas_hoy": ventas.filter(creada_en__date=date.today()).count(),
            "ingresos": ventas.filter(estado=Venta.Estado.ACEPTADA).aggregate(total=Sum("total"))["total"] or 0,
            "ultimas_ventas": ventas.select_related("producto", "vendedor")[:5],
            "es_administrador": es_administrador(self.request.user),
        })
        return context


class ProductoListView(SoloAdministradorMixin, ListView):
    model = Producto
    template_name = "inventario/lista.html"
    context_object_name = "productos"


class ProductoCreateView(SoloAdministradorMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/formulario.html"
    success_url = reverse_lazy("inventario:lista")

    def form_valid(self, form):
        messages.success(self.request, "Producto creado correctamente.")
        return super().form_valid(form)


class ProductoUpdateView(SoloAdministradorMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/formulario.html"
    success_url = reverse_lazy("inventario:lista")

    def form_valid(self, form):
        messages.success(self.request, "Producto actualizado correctamente.")
        return super().form_valid(form)


class ProductoDeleteView(SoloAdministradorMixin, DeleteView):
    model = Producto
    template_name = "inventario/confirmar_eliminar.html"
    success_url = reverse_lazy("inventario:lista")

    def form_valid(self, form):
        messages.success(self.request, "Producto eliminado correctamente.")
        return super().form_valid(form)


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
        ventas = Venta.objects.select_related("producto", "vendedor")
        return ventas if es_administrador(self.request.user) else ventas.filter(vendedor=self.request.user)
