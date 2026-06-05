from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0015_seed_scrapingsources"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scrapingsource",
            name="offer_type",
        ),
    ]
