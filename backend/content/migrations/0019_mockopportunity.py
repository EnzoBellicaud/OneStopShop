import uuid as _uuid

from django.db import migrations, models

_SEEDED_KEYS = [
    "unibz", "mdu", "tu_ilmenau", "utc",
    "euc", "uitm", "univpm", "unmo", "ipvc",
]


def disable_seeded_sources(apps, schema_editor):
    ScrapingSource = apps.get_model("content", "ScrapingSource")
    ScrapingSource.objects.filter(key__in=_SEEDED_KEYS).update(enabled=False)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("content", "0018_seed_offertype_keywords")]
    operations = [
        migrations.CreateModel(
            name="MockOpportunity",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=_uuid.uuid4, editable=False, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("offer_type", models.CharField(default="internship", max_length=50)),
                ("target_profile", models.CharField(default="student", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "content_mockopportunity", "ordering": ["-created_at"], "verbose_name_plural": "mock opportunities"},
        ),
        migrations.RunPython(disable_seeded_sources, reverse_code=noop),
    ]
