from django.db import migrations


def install_protection(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('''
            CREATE OR REPLACE FUNCTION agenda_proteger_identidad_fn() RETURNS trigger AS $$
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'Los expedientes no se pueden eliminar';
                END IF;
                IF OLD.numero IS DISTINCT FROM NEW.numero
                   OR OLD.anio IS DISTINCT FROM NEW.anio
                   OR OLD.codigo_reparticion IS DISTINCT FROM NEW.codigo_reparticion THEN
                    RAISE EXCEPTION 'La identidad oficial del expediente no se puede modificar';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')
        cursor.execute('''
            CREATE TRIGGER agenda_proteger_identidad
            BEFORE UPDATE OR DELETE ON agenda
            FOR EACH ROW EXECUTE FUNCTION agenda_proteger_identidad_fn();
        ''')


def remove_protection(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP TRIGGER IF EXISTS agenda_proteger_identidad ON agenda;')
        cursor.execute('DROP FUNCTION IF EXISTS agenda_proteger_identidad_fn();')


class Migration(migrations.Migration):
    dependencies = [('agenda', '0002_codigo_reparticion_y_identidad_oficial')]

    operations = [migrations.RunPython(install_protection, remove_protection)]
