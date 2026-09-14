from django.contrib import admin

from .models import Compra, Producto, Venta


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo_barras", "precio", "stock", "actualizado_en")
    search_fields = ("nombre", "codigo_barras")


class VentaInline(admin.TabularInline):
    model = Venta
    extra = 0
    fields = ("producto", "cantidad", "precio_unitario", "total", "estado")
    readonly_fields = ("total",)


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("id", "vendedor", "metodo_pago", "total", "creada_en")
    list_filter = ("metodo_pago", "creada_en")
    search_fields = ("vendedor__username",)
    readonly_fields = ("creada_en",)
    inlines = (VentaInline,)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("producto", "cantidad", "compra", "total", "estado", "vendedor", "creada_en")
    list_filter = ("estado", "creada_en")
    search_fields = ("producto__nombre", "vendedor__username")
    readonly_fields = ("creada_en",)
