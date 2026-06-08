from django.db import migrations

KEYWORDS = {
    "thesis": "examensarbete, abschlussarbeit, mémoire, tesi di laurea, trabalho de conclusão, dissertation, doktorarbeit",
    "internship": "stage, praktik, tirocinio, estágio, Praktikum, stagiaire, pratica",
    "scholarship": "stipendium, bourse, borsa di studio, bolsa, stipendio, beca, studienbörse",
    "job": "emploi, stelle, lavoro, emprego, jobb, arbeit, offre d emploi",
    "course": "kurs, cours, corso, kurso, opleiding, formation, ausbildung",
    "exchange": "échange, scambio, intercâmbio, Austausch, utbyte, erasmus",
    "competition": "tävling, concours, concorso, competição, Wettbewerb, hackathon",
    "volunteer": "volontariat, volontariato, voluntariado, Ehrenamt, frivillig",
}


def seed_keywords(apps, schema_editor):
    OfferType = apps.get_model("content", "OfferType")
    for name, kw in KEYWORDS.items():
        OfferType.objects.filter(name=name).update(keywords=kw)


class Migration(migrations.Migration):
    dependencies = [("content", "0017_offertype_keywords")]

    operations = [migrations.RunPython(seed_keywords, migrations.RunPython.noop)]
