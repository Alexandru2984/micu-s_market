import os

from django.db import migrations


def set_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    domain = os.getenv("DJANGO_SITE_DOMAIN", "market.micutu.com")
    Site.objects.update_or_create(
        pk=1, defaults={"domain": domain, "name": "Micu's Market"}
    )


def revert(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.filter(pk=1).update(domain="example.com", name="example.com")


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(set_site, revert),
    ]
