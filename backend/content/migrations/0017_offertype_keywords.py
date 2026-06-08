from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0016_remove_scrapingsource_offer_type")]

    operations = [
        migrations.AddField(
            model_name="offertype",
            name="keywords",
            field=models.TextField(blank=True, default=""),
        ),
    ]
