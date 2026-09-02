from django import forms

from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ("nombre", "precio", "stock")
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej. Kombucha"}),
            "precio": forms.NumberInput(attrs={"min": 0}),
            "stock": forms.NumberInput(attrs={"min": 0}),
        }


class VentaForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.none(), empty_label="Selecciona un producto")
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"min": 1}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True, stock__gt=0).order_by("nombre")
