from django.contrib import admin

from .models import Producto, Venta


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "actualizado_en")
    search_fields = ("nombre",)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("producto", "cantidad", "total", "estado", "vendedor", "creada_en")
    list_filter = ("estado", "creada_en")
    search_fields = ("producto__nombre", "vendedor__username")
    readonly_fields = ("creada_en",)
