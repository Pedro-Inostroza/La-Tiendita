from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Producto, Venta


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

    def test_venta_descuenta_stock_y_registra_usuario(self):
        self.client.force_login(self.vendedor)
        response = self.client.post(reverse("ventas:registrar"), {
            "producto": self.producto.pk, "cantidad": 3,
        })
        self.assertRedirects(response, reverse("ventas:lista"))
        self.producto.refresh_from_db()
        venta = Venta.objects.get()
        self.assertEqual(self.producto.stock, 7)
        self.assertEqual(venta.total, 7500)
        self.assertEqual(venta.vendedor, self.vendedor)

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
        self.assertContains(response, "$16000")
        self.assertContains(response, "Lunes")
        self.assertContains(response, "4 unidades vendidas")
        self.assertContains(response, "Kombucha")
        self.assertNotContains(response, "$46000")
