from django.db import migrations


def crear_roles_y_catalogo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Producto = apps.get_model("core", "Producto")
    Group.objects.get_or_create(name="Administrador")
    Group.objects.get_or_create(name="Vendedor")
    productos = [
        ("Kombucha", 2500, 20),
        ("Electrolit", 3000, 15),
        ("Agua de coco 500ml", 3000, 18),
        ("Jugo bless", 2500, 12),
        ("Mantequilla de almendras", 8990, 6),
    ]
    for nombre, precio, stock in productos:
        Producto.objects.get_or_create(nombre=nombre, defaults={"precio": precio, "stock": stock})


def borrar_roles_y_catalogo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Producto = apps.get_model("core", "Producto")
    Group.objects.filter(name__in=["Administrador", "Vendedor"]).delete()
    Producto.objects.filter(nombre__in=["Kombucha", "Electrolit", "Agua de coco 500ml", "Jugo bless", "Mantequilla de almendras"]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(crear_roles_y_catalogo, borrar_roles_y_catalogo)]
