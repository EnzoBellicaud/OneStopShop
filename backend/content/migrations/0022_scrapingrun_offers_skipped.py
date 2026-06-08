from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0021_offertype_keywords_all"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrapingrun",
            name="offers_skipped",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
