import uuid

import django.db.models.deletion
from django.db import migrations, models

NS = uuid.UUID("7fb7cb8f-9536-41f6-a908-80fa31d8dc2d")


def populate_org_fk(apps, schema_editor):
    ScrapingSource = apps.get_model("content", "ScrapingSource")
    Organization = apps.get_model("content", "Organization")
    for src in ScrapingSource.objects.all():
        if src.organization_token:
            org_id = uuid.uuid5(NS, src.organization_token)
            try:
                src.organization = Organization.objects.get(id=org_id)
                src.save(update_fields=["organization"])
            except Organization.DoesNotExist:
                pass


class Migration(migrations.Migration):
    dependencies = [("content", "0022_scrapingrun_offers_skipped")]

    operations = [
        migrations.AddField(
            model_name="scrapingsource",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="scraping_sources",
                to="content.organization",
            ),
        ),
        migrations.RunPython(populate_org_fk, migrations.RunPython.noop),
    ]
