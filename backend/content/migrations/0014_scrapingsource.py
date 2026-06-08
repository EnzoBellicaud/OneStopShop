from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0013_teacher_profile_approval_allowed_domain"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScrapingSource",
            fields=[
                ("key", models.CharField(max_length=100, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("url", models.URLField(max_length=500)),
                ("organization_token", models.CharField(max_length=100)),
                ("offer_type", models.CharField(max_length=100, default="")),
                ("target_profile", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=10)),
                ("domain_names", models.JSONField(default=list)),
                ("interval_minutes", models.IntegerField(default=360)),
                ("llm_fallback_enabled", models.BooleanField(default=True)),
                ("enabled", models.BooleanField(default=True)),
                ("quality", models.CharField(default="real", max_length=50)),
                ("crawl_enabled", models.BooleanField(default=False)),
                ("crawl_depth", models.IntegerField(default=1)),
                ("crawl_max_pages", models.IntegerField(default=25)),
                ("crawl_match_patterns", models.JSONField(default=list)),
                ("crawl_exclude_patterns", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "content_scrapingsource",
                "ordering": ["key"],
            },
        ),
    ]
