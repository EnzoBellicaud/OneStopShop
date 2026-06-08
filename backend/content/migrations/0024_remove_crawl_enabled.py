from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("content", "0023_scrapingsource_organization_fk")]
    operations = [
        migrations.RemoveField(model_name="scrapingsource", name="crawl_enabled"),
    ]
