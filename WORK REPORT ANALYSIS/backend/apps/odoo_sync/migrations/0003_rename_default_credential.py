from django.db import migrations


def rename_default_to_connection_1(apps, schema_editor):
    OdooCredential = apps.get_model('odoo_sync', 'OdooCredential')
    for cred in OdooCredential.objects.filter(name='Default'):
        if OdooCredential.objects.filter(user=cred.user, name='Connection 1').exists():
            # User already has a proper Connection 1 — delete the stale Default
            cred.delete()
        else:
            cred.name = 'Connection 1'
            cred.save()


class Migration(migrations.Migration):

    dependencies = [
        ('odoo_sync', '0002_odoocredential_name_alter_odoocredential_user'),
    ]

    operations = [
        migrations.RunPython(rename_default_to_connection_1, migrations.RunPython.noop),
    ]
