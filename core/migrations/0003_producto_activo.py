from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_roles_y_catalogo_inicial"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="activo",
            field=models.BooleanField(default=True),
        ),
    ]
