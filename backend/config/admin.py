from django.contrib.admin.apps import AdminConfig


class RegistroAdminConfig(AdminConfig):
    default_site = 'config.admin_site.RegistroAdminSite'
