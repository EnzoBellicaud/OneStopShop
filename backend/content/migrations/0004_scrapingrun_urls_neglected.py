from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0003_scrapingjob_scrapingrun"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrapingrun",
            name="urls_neglected",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
