from django.conf import settings
from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    codigo_barras = models.CharField(max_length=64, unique=True, blank=True, null=True)
    precio = models.PositiveIntegerField(help_text="Precio en pesos chilenos")
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    class MetodoPago(models.TextChoices):
        DEBITO = "DEBITO", "Débito"
        CREDITO = "CREDITO", "Crédito"
        EFECTIVO = "EFECTIVO", "Efectivo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"

    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="compras")
    metodo_pago = models.CharField(max_length=15, choices=MetodoPago.choices)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Compra #{self.pk}"

    @property
    def total(self):
        return self.ventas.aggregate(total=models.Sum("total"))["total"] or 0


class Venta(models.Model):
    class Estado(models.TextChoices):
        ACEPTADA = "ACEPTADA", "Aceptada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        INVALIDA = "INVALIDA", "Dato inválido"

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="ventas", null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="ventas")
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.PositiveIntegerField()
    total = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=12, choices=Estado.choices)
    motivo = models.CharField(max_length=255, blank=True)
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ventas")
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.producto} × {self.cantidad}"
