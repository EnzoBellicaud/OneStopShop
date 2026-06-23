from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0025_contact_linkedin")]

    operations = [
        migrations.AddField(
            model_name="scrapingsource",
            name="auto_publish_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
