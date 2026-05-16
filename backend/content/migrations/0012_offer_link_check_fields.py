from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_offer_deadline"),
    ]

    operations = [
        migrations.AddField(
            model_name="offer",
            name="link_errors",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="offer",
            name="link_last_checked",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
