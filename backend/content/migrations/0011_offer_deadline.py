from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0010_forumquestion_forumanswer"),
    ]

    operations = [
        migrations.AddField(
            model_name="offer",
            name="deadline",
            field=models.DateField(blank=True, null=True),
        ),
    ]
