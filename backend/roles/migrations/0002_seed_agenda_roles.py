from django.db import migrations


def seed_roles(apps, schema_editor):
    role = apps.get_model('roles', 'Rol')
    for name in ('CONSULTOR', 'ADMINISTRATIVO', 'ADMINISTRADOR'):
        role.objects.using(schema_editor.connection.alias).get_or_create(descripcion=name)


class Migration(migrations.Migration):
    dependencies = [('roles', '0001_initial')]
    operations = [migrations.RunPython(seed_roles, migrations.RunPython.noop)]
