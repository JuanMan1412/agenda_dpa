from django.db import migrations


def allow_letter_edits(apps, schema_editor):
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
                    RAISE EXCEPTION 'El numero, el anio y el codigo de reparticion no se pueden modificar';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')


def protect_letter_again(apps, schema_editor):
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
                   OR OLD.codigo_reparticion IS DISTINCT FROM NEW.codigo_reparticion
                   OR OLD.letra IS DISTINCT FROM NEW.letra THEN
                    RAISE EXCEPTION 'La identidad oficial del expediente no se puede modificar';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')


class Migration(migrations.Migration):
    dependencies = [('agenda', '0003_proteger_identidad_expediente')]
    operations = [migrations.RunPython(allow_letter_edits, protect_letter_again)]
