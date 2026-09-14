from django import forms
from django.forms import formset_factory

from .models import Compra, Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ("nombre", "codigo_barras", "precio", "stock")
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej. Kombucha"}),
            "codigo_barras": forms.TextInput(attrs={"placeholder": "Ej. 7801234567890"}),
            "precio": forms.NumberInput(attrs={"min": 0}),
            "stock": forms.NumberInput(attrs={"min": 0}),
        }

    def clean_codigo_barras(self):
        return self.cleaned_data["codigo_barras"] or None


class CompraForm(forms.Form):
    metodo_pago = forms.ChoiceField(label="Tipo de pago", choices=Compra.MetodoPago.choices)


class VentaItemForm(forms.Form):
    codigo_barras = forms.CharField(
        label="Código de barras",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Escanea o escribe el código"}),
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(), empty_label="Selecciona un producto", required=False
    )
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"min": 1}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True, stock__gt=0).order_by("nombre")

    def clean(self):
        cleaned_data = super().clean()
        codigo_barras = (cleaned_data.get("codigo_barras") or "").strip()
        producto = cleaned_data.get("producto")
        if codigo_barras:
            try:
                producto = Producto.objects.get(codigo_barras=codigo_barras, activo=True, stock__gt=0)
            except Producto.DoesNotExist:
                self.add_error("codigo_barras", "No se encontró un producto activo con ese código de barras.")
            else:
                cleaned_data["producto"] = producto
        elif not producto:
            self.add_error("producto", "Selecciona un producto o escanea un código de barras.")
        return cleaned_data


VentaItemFormSet = formset_factory(VentaItemForm, extra=1, can_delete=True)
