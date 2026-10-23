from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('agenda', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='agenda',
            name='codigo_reparticion',
            field=models.CharField(blank=True, default='', editable=False, max_length=20),
        ),
        migrations.RemoveConstraint(
            model_name='agenda',
            name='expediente_numero_anio_unico',
        ),
        migrations.AddConstraint(
            model_name='agenda',
            constraint=models.UniqueConstraint(
                fields=('numero', 'codigo_reparticion', 'letra', 'anio'),
                name='expediente_identidad_oficial_unica',
            ),
        ),
    ]
