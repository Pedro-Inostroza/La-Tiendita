from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import VentaItemForm
from .models import Compra, FormaPago, Producto, Venta


class SeguridadYVentasTests(TestCase):
    def setUp(self):
        self.producto, _ = Producto.objects.update_or_create(
            nombre="Kombucha", defaults={"precio": 2500, "stock": 10}
        )
        self.vendedor = User.objects.create_user(username="vendedor", password="clave-segura")
        self.admin = User.objects.create_user(username="admin", password="clave-segura", is_staff=True)
        vendedores, _ = Group.objects.get_or_create(name="Vendedor")
        administradores, _ = Group.objects.get_or_create(name="Administrador")
        self.vendedor.groups.add(vendedores)
        self.admin.groups.add(administradores)

    def _post_venta(self, items, formas_pago):
        data = {
            "form-TOTAL_FORMS": str(len(items)),
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "pago-TOTAL_FORMS": str(len(formas_pago)),
            "pago-INITIAL_FORMS": "0",
            "pago-MIN_NUM_FORMS": "0",
            "pago-MAX_NUM_FORMS": "1000",
        }
        for index, item in enumerate(items):
            for key, value in item.items():
                data[f"form-{index}-{key}"] = value
        for index, forma in enumerate(formas_pago):
            for key, value in forma.items():
                data[f"pago-{index}-{key}"] = value
        return self.client.post(reverse("ventas:registrar"), data)

    def test_inicio_muestra_login(self):
        response = self.client.get("/")
        self.assertContains(response, "Ingresa con tu cuenta")

    def test_vendedor_puede_modificar_stock_y_precio(self):
        self.client.force_login(self.vendedor)
        response = self.client.post(reverse("inventario:editar", args=[self.producto.pk]), {
            "nombre": "Kombucha", "precio": 2800, "stock": 25,
        })
        self.assertRedirects(response, reverse("inventario:lista"))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.precio, 2800)
        self.assertEqual(self.producto.stock, 25)

    def test_administrador_puede_crear_producto(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventario:crear"), {
            "nombre": "Granola", "precio": 4500, "stock": 12,
        })
        self.assertRedirects(response, reverse("inventario:lista"))
        self.assertTrue(Producto.objects.filter(nombre="Granola").exists())

    def test_vendedor_puede_crear_producto(self):
        self.client.force_login(self.vendedor)
        response = self.client.post(reverse("inventario:crear"), {
            "nombre": "Granola", "precio": 4500, "stock": 12,
        })
        self.assertRedirects(response, reverse("inventario:lista"))
        self.assertTrue(Producto.objects.filter(nombre="Granola").exists())

    def test_vendedor_no_puede_cambiar_estado_de_producto(self):
        self.client.force_login(self.vendedor)

        response = self.client.post(reverse("inventario:cambiar_estado", args=[self.producto.pk]))

        self.assertRedirects(response, reverse("dashboard"))
        self.producto.refresh_from_db()
        self.assertTrue(self.producto.activo)

    def test_formulario_de_venta_muestra_pago_primero_y_buscador_global(self):
        self.client.force_login(self.vendedor)

        response = self.client.get(reverse("ventas:registrar"))

        contenido = response.content.decode()
        self.assertContains(response, 'id="buscador-global"')
        self.assertContains(response, 'class="opciones-pago"')
        self.assertContains(response, 'type="radio"')
        # El metodo de pago se muestra antes que el listado de productos.
        self.assertLess(contenido.index("1. Método de pago"), contenido.index("2. Productos"))
        # Ya no hay una barra de codigo de barras por cada fila de producto.
        self.assertNotContains(response, "Escanea o escribe el código")

    def test_venta_descuenta_stock_y_registra_usuario(self):
        self.client.force_login(self.vendedor)
        response = self._post_venta(
            [{"producto": self.producto.pk, "cantidad": 3}],
            [{"tipo": FormaPago.Tipo.EFECTIVO, "monto": 7500}],
        )
        self.assertRedirects(response, reverse("ventas:lista"))
        self.producto.refresh_from_db()
        compra = Compra.objects.get()
        venta = Venta.objects.get()
        self.assertEqual(self.producto.stock, 7)
        self.assertEqual(venta.total, 7500)
        self.assertEqual(venta.vendedor, self.vendedor)
        self.assertEqual(venta.compra, compra)
        self.assertEqual(compra.total_pagado, 7500)
        self.assertEqual(compra.formas_pago.count(), 1)
        self.assertEqual(compra.formas_pago.get().tipo, FormaPago.Tipo.EFECTIVO)

    def test_venta_por_codigo_de_barras_selecciona_producto(self):
        self.producto.codigo_barras = "7801234567890"
        self.producto.save(update_fields=["codigo_barras"])
        self.client.force_login(self.vendedor)
        response = self._post_venta(
            [{"codigo_barras": "7801234567890", "cantidad": 2}],
            [{"tipo": FormaPago.Tipo.DEBITO, "monto": 5000}],
        )
        self.assertRedirects(response, reverse("ventas:lista"))
        venta = Venta.objects.get()
        self.assertEqual(venta.producto, self.producto)
        self.assertEqual(venta.compra.formas_pago.get().tipo, FormaPago.Tipo.DEBITO)

    def test_venta_admite_varios_productos_en_una_sola_compra(self):
        producto_secundario = Producto.objects.create(nombre="Granola", precio=3000, stock=10)
        self.client.force_login(self.vendedor)
        response = self._post_venta(
            [
                {"producto": self.producto.pk, "cantidad": 2},
                {"producto": producto_secundario.pk, "cantidad": 4},
            ],
            [{"tipo": FormaPago.Tipo.TRANSFERENCIA, "monto": 17000}],
        )
        self.assertRedirects(response, reverse("ventas:lista"))
        compra = Compra.objects.get()
        self.assertEqual(compra.ventas.count(), 2)
        self.assertEqual(compra.total, 2 * 2500 + 4 * 3000)
        self.producto.refresh_from_db()
        producto_secundario.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)
        self.assertEqual(producto_secundario.stock, 6)

    def test_venta_admite_varias_formas_de_pago(self):
        self.client.force_login(self.vendedor)
        response = self._post_venta(
            [{"producto": self.producto.pk, "cantidad": 3}],
            [
                {"tipo": FormaPago.Tipo.EFECTIVO, "monto": 5000},
                {"tipo": FormaPago.Tipo.DEBITO, "monto": 2500},
            ],
        )
        self.assertRedirects(response, reverse("ventas:lista"))
        compra = Compra.objects.get()
        self.assertEqual(compra.total, 7500)
        self.assertEqual(compra.total_pagado, 7500)
        self.assertEqual(compra.formas_pago.count(), 2)
        tipos = set(compra.formas_pago.values_list("tipo", flat=True))
        self.assertEqual(tipos, {FormaPago.Tipo.EFECTIVO, FormaPago.Tipo.DEBITO})

    def test_venta_falla_si_el_pago_no_cubre_el_total(self):
        self.client.force_login(self.vendedor)
        response = self._post_venta(
            [{"producto": self.producto.pk, "cantidad": 3}],
            [{"tipo": FormaPago.Tipo.EFECTIVO, "monto": 5000}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no cubre el total")
        self.assertFalse(Compra.objects.exists())
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_venta_falla_completa_si_un_producto_no_tiene_stock(self):
        producto_secundario = Producto.objects.create(nombre="Granola", precio=3000, stock=1)
        self.client.force_login(self.vendedor)
        response = self._post_venta(
            [
                {"producto": self.producto.pk, "cantidad": 2},
                {"producto": producto_secundario.pk, "cantidad": 5},
            ],
            [{"tipo": FormaPago.Tipo.EFECTIVO, "monto": 999999}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Compra.objects.exists())
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_retirar_producto_lo_inactiva_y_lo_excluye_de_las_ventas(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("inventario:cambiar_estado", args=[self.producto.pk]))

        self.assertRedirects(response, reverse("inventario:lista"))
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)
        self.assertNotIn(self.producto, VentaItemForm().fields["producto"].queryset)

    def test_dashboard_cuenta_solo_productos_activos(self):
        Producto.objects.create(nombre="Retirado", precio=3000, stock=2, activo=False)
        self.producto.activo = False
        self.producto.save(update_fields=["activo"])
        self.client.force_login(self.vendedor)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.context["total_productos"], Producto.objects.filter(activo=True).count())
        self.assertEqual(response.context["stock_bajo"], Producto.objects.filter(activo=True, stock__lte=5).count())
        self.assertContains(response, "Productos activos")

    def test_dashboard_muestra_analisis_estadistico_de_ventas_aceptadas(self):
        producto_secundario = Producto.objects.create(nombre="Granola", precio=3000, stock=10)
        venta_principal = Venta.objects.create(producto=self.producto, cantidad=4, precio_unitario=2500,
                                               total=10000, estado=Venta.Estado.ACEPTADA, vendedor=self.vendedor)
        venta_secundaria = Venta.objects.create(producto=producto_secundario, cantidad=2, precio_unitario=3000,
                                                total=6000, estado=Venta.Estado.ACEPTADA, vendedor=self.vendedor)
        Venta.objects.create(producto=producto_secundario, cantidad=10, precio_unitario=3000,
                             total=30000, estado=Venta.Estado.RECHAZADA, vendedor=self.vendedor)
        lunes = timezone.now() - timedelta(days=timezone.now().weekday())
        venta_principal.creada_en = lunes
        venta_principal.save(update_fields=["creada_en"])
        venta_secundaria.creada_en = lunes + timedelta(days=1)
        venta_secundaria.save(update_fields=["creada_en"])

        self.client.force_login(self.vendedor)
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Análisis estadístico")
        self.assertContains(response, "$16.000")
        self.assertContains(response, "Lunes")
        self.assertContains(response, "4 unidades vendidas")
        self.assertContains(response, "Kombucha")
        self.assertNotContains(response, "$46.000")
