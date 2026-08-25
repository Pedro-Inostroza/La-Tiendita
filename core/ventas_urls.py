from django.urls import path

from . import views

app_name = "ventas"

urlpatterns = [
    path("", views.VentaListView.as_view(), name="lista"),
    path("nueva/", views.registrar_venta, name="registrar"),
]
