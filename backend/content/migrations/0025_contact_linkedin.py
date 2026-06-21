from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0024_remove_crawl_enabled")]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="linkedin",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
