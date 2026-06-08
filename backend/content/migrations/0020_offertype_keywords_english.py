"""Add English base terms to offer type keywords so the TF-IDF classifier
can match English-language pages (including the mock demo site)."""
from django.db import migrations

_ENGLISH_ADDITIONS = {
    "internship": "internship, intern, placement, work experience, traineeship",
    "thesis":     "thesis, dissertation, final project, capstone, research project, master thesis, bachelor thesis",
    "scholarship": "scholarship, grant, fellowship, bursary, financial aid, funding",
    "job":        "job, position, vacancy, employment, career, full-time, part-time, hiring",
    "course":     "course, class, training, programme, program, workshop, seminar, lecture",
    "exchange":   "exchange, mobility, abroad, semester abroad, study abroad",
}


def add_english_keywords(apps, schema_editor):
    OfferType = apps.get_model("content", "OfferType")
    for name, additions in _ENGLISH_ADDITIONS.items():
        obj = OfferType.objects.filter(name=name).first()
        if obj is None:
            continue
        existing = obj.keywords or ""
        if existing:
            obj.keywords = existing + ", " + additions
        else:
            obj.keywords = additions
        obj.save(update_fields=["keywords"])


class Migration(migrations.Migration):
    dependencies = [("content", "0019_mockopportunity")]
    operations = [migrations.RunPython(add_english_keywords, migrations.RunPython.noop)]
