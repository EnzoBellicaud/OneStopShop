from django.db import migrations


def seed_sources(apps, schema_editor):
    ScrapingSource = apps.get_model("content", "ScrapingSource")
    from content.scrapers.source_registry import SOURCE_REGISTRY

    for s in SOURCE_REGISTRY:
        ScrapingSource.objects.get_or_create(
            key=s.key,
            defaults=dict(
                name=s.name,
                url=s.url,
                organization_token=s.organization_token,
                target_profile=s.target_profile,
                country=s.country,
                domain_names=s.domain_names,
                interval_minutes=s.interval_minutes,
                llm_fallback_enabled=s.llm_fallback_enabled,
                enabled=s.enabled,
                quality=s.quality,
                crawl_enabled=s.crawl_enabled,
                crawl_depth=s.crawl_depth,
                crawl_max_pages=s.crawl_max_pages,
                crawl_match_patterns=list(s.crawl_match_patterns),
                crawl_exclude_patterns=list(s.crawl_exclude_patterns),
            ),
        )


def unseed_sources(apps, schema_editor):
    ScrapingSource = apps.get_model("content", "ScrapingSource")
    ScrapingSource.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0014_scrapingsource"),
    ]

    operations = [
        migrations.RunPython(seed_sources, reverse_code=unseed_sources),
    ]
