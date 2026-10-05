from django.db import migrations


def install_protection(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute("""
        CREATE OR REPLACE FUNCTION proteger_expediente_dpa() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Los registros administrativos no se eliminan; deben anularse';
            END IF;
            IF NEW.numero <> OLD.numero OR NEW.anio <> OLD.anio THEN
                RAISE EXCEPTION 'El numero y el anio del expediente son inmutables';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    schema_editor.execute('CREATE TRIGGER proteger_expediente_dpa BEFORE DELETE OR UPDATE ON agenda FOR EACH ROW EXECUTE FUNCTION proteger_expediente_dpa()')


class Migration(migrations.Migration):
    dependencies = [('agenda', '0004_agenda_anio_agenda_anulado_agenda_anulado_por_and_more')]
    operations = [migrations.RunPython(install_protection)]
