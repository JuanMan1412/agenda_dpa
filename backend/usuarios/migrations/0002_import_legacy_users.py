from django.core.management.color import no_style
from django.db import migrations


def rows(connection, table):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM {connection.ops.quote_name(table)}')
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def import_legacy_users(apps, schema_editor):
    connection = schema_editor.connection
    tables = connection.introspection.table_names()
    if 'auth_user' not in tables:
        return
    User = apps.get_model('usuarios', 'User')
    Rol = apps.get_model('roles', 'Rol')
    alias = connection.alias
    profiles = {}
    if 'portal_accounts_portalprofile' in tables:
        profiles = {row['user_id']: row for row in rows(connection, 'portal_accounts_portalprofile')}
    for row in rows(connection, 'auth_user'):
        existing = User.objects.using(alias).filter(pk=row['id']).first()
        if existing:
            if existing.username != row['username']:
                raise RuntimeError('Colision de ID al trasladar usuarios; no se modificaron cuentas existentes.')
            continue
        if User.objects.using(alias).filter(username=row['username']).exists():
            raise RuntimeError('Colision de username al trasladar usuarios; revisar la vinculacion manualmente.')
        profile = profiles.get(row['id'], {})
        role = None
        if profile.get('rol'):
            role, _ = Rol.objects.using(alias).get_or_create(descripcion=profile['rol'])
        User.objects.using(alias).create(
            id=row['id'], username=row['username'], password=row['password'],
            email=row['email'], nombre=row['first_name'], apellido=row['last_name'],
            nombre_completo=profile.get('nombre_completo', ''),
            portal_user_id=profile.get('portal_user_id'), rol=role,
            is_active=row['is_active'], is_staff=row['is_staff'], is_superuser=row['is_superuser'],
            date_joined=row['date_joined'], last_login=row['last_login'],
        )
    for legacy_table, field, identity_field in (
        ('auth_user_groups', 'groups', 'group_id'),
        ('auth_user_user_permissions', 'user_permissions', 'permission_id'),
    ):
        if legacy_table in tables:
            for row in rows(connection, legacy_table):
                getattr(User.objects.using(alias).get(pk=row['user_id']), field).add(row[identity_field])
    # Mantener IDs evita cambiar las sesiones/JWT locales y las entradas del admin.
    if 'django_admin_log' in tables:
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, 'django_admin_log')
        old_constraints = [name for name, value in constraints.items() if value.get('foreign_key') == ('auth_user', 'id')]
        if old_constraints and connection.vendor == 'postgresql':
            for name in old_constraints:
                schema_editor.execute(f'ALTER TABLE django_admin_log DROP CONSTRAINT {schema_editor.quote_name(name)}')
            schema_editor.execute('ALTER TABLE django_admin_log ADD CONSTRAINT django_admin_log_usuarios_user_fk FOREIGN KEY (user_id) REFERENCES usuarios_user(id) DEFERRABLE INITIALLY DEFERRED')
        elif old_constraints:
            raise RuntimeError('La conversion de una base existente requiere PostgreSQL.')
    for sql in connection.ops.sequence_reset_sql(no_style(), [User, Rol]):
        schema_editor.execute(sql)
    # Las tablas anteriores quedan como respaldo; no se borran datos historicos.


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0001_initial'),
        ('roles', '0002_seed_agenda_roles'),
        ('admin', '0003_logentry_add_action_flag_choices'),
    ]
    operations = [migrations.RunPython(import_legacy_users, migrations.RunPython.noop)]
