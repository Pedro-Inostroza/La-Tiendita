from unittest.mock import patch

from django.test import TestCase


class ResumenTests(TestCase):
    def setUp(self):
        self.catalogo = {
            "Kombucha": {"precio": 2500, "stock": 20},
        }

    @patch("core.views.guardar_catalogo")
    @patch("core.views.cargar_catalogo")
    def test_agregar_producto(self, cargar_catalogo, guardar_catalogo):
        cargar_catalogo.return_value = self.catalogo

        response = self.client.post("/", {
            "accion": "agregar_producto",
            "nuevo_producto": "Granola",
            "nuevo_precio": "4500",
            "nuevo_stock": "12",
        })

        self.assertRedirects(response, "/")
        self.assertEqual(self.catalogo["Granola"], {"precio": 4500, "stock": 12})
        guardar_catalogo.assert_called_once_with(self.catalogo)

    @patch("core.views.guardar_catalogo")
    @patch("core.views.cargar_catalogo")
    def test_modificar_precio_y_stock(self, cargar_catalogo, guardar_catalogo):
        cargar_catalogo.return_value = self.catalogo

        response = self.client.post("/", {
            "accion": "editar_producto",
            "producto": "Kombucha",
            "precio": "2900",
            "stock": "30",
        })

        self.assertRedirects(response, "/")
        self.assertEqual(self.catalogo["Kombucha"], {"precio": 2900, "stock": 30})
        guardar_catalogo.assert_called_once_with(self.catalogo)

    @patch("core.views.guardar_catalogo")
    @patch("core.views.cargar_catalogo")
    def test_eliminar_producto(self, cargar_catalogo, guardar_catalogo):
        cargar_catalogo.return_value = self.catalogo

        response = self.client.post("/", {
            "accion": "eliminar_producto",
            "producto": "Kombucha",
        })

        self.assertRedirects(response, "/")
        self.assertNotIn("Kombucha", self.catalogo)
        guardar_catalogo.assert_called_once_with(self.catalogo)
