from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

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

    def test_vendedor_no_puede_administrar_productos(self):
        self.client.force_login(self.vendedor)
        response = self.client.get(reverse("inventario:lista"))
        self.assertEqual(response.status_code, 403)

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
