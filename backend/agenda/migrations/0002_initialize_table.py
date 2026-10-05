from django.db import migrations


def initialize_agenda(apps, schema_editor):
    if 'agenda' in schema_editor.connection.introspection.table_names():
        return
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('CREATE SEQUENCE IF NOT EXISTS agenda_numero_seq START WITH 1')
        schema_editor.execute("""
            CREATE TABLE agenda (
                id SERIAL PRIMARY KEY,
                numero INTEGER NOT NULL UNIQUE DEFAULT nextval('agenda_numero_seq'),
                letra VARCHAR(10) NOT NULL,
                origen VARCHAR(12) NOT NULL CHECK (origen IN ('manual', 'automatico')),
                referencia_externa VARCHAR(100),
                fecha_hora TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        schema_editor.execute('ALTER SEQUENCE agenda_numero_seq OWNED BY agenda.numero')
    else:
        # Las pruebas usan SQLite; en desarrollo/produccion se utiliza PostgreSQL.
        schema_editor.create_model(apps.get_model('agenda', 'Agenda'))


class Migration(migrations.Migration):
    dependencies = [('agenda', '0001_initial')]
    operations = [migrations.RunPython(initialize_agenda, migrations.RunPython.noop)]
