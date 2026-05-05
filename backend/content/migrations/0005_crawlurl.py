import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0004_scrapingrun_urls_neglected"),
    ]

    operations = [
        migrations.CreateModel(
            name="CrawlUrl",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_key", models.CharField(max_length=120)),
                ("url", models.URLField(max_length=2048)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("processing", "Processing"),
                        ("done", "Done"),
                        ("error", "Error"),
                        ("archived", "Archived"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("offer", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="crawl_urls",
                    to="content.offer",
                )),
                ("next_check_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_scraped_at", models.DateTimeField(blank=True, null=True)),
                ("consecutive_errors", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True)),
                ("last_http_status", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={"db_table": "crawl_url"},
        ),
        migrations.AlterUniqueTogether(
            name="crawlurl",
            unique_together={("source_key", "url")},
        ),
        migrations.AddIndex(
            model_name="crawlurl",
            index=models.Index(fields=["status", "next_check_at"], name="idx_crawlurl_status_next_check"),
        ),
        migrations.AddIndex(
            model_name="crawlurl",
            index=models.Index(fields=["source_key"], name="idx_crawlurl_source"),
        ),
    ]
