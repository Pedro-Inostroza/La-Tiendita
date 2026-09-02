from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("productos/", views.ProductoListView.as_view(), name="lista"),
    path("productos/nuevo/", views.ProductoCreateView.as_view(), name="crear"),
    path("productos/<int:pk>/editar/", views.ProductoUpdateView.as_view(), name="editar"),
    path("productos/<int:pk>/estado/", views.producto_cambiar_estado, name="cambiar_estado"),
]
