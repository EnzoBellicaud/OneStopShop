"""Seed keywords for all offer types that currently have none.
Covers challenge, co_creation, funding_partner, hackathon, lab,
project_opportunity, research_group, service, testbed, training.
Internship and thesis already have keywords (set by 0018 + 0020).
"""
from django.db import migrations

_KEYWORDS = {
    "challenge": (
        "challenge, open challenge, open call, call for solutions, competition, contest, prize, "
        "problem-solving, open innovation, challenge-based learning, "
        "defi, Herausforderung, sfida, desafio, tävling, Wettbewerb, concours, concorso, "
        "competição, gara, izazov"
    ),
    "co_creation": (
        "co-creation, co creation, collaboration, partnership, joint project, co-design, "
        "innovation partnership, spin-off, joint venture, co-develop, consortium, "
        "collaborazione, samarbete, zusammenarbeit, coopération, parceria, colaboración, "
        "samenwerking, innovazione congiunta, coinnovation"
    ),
    "funding_partner": (
        "funding, grant, financial support, research funding, call for proposals, "
        "doctoral funding, DIN, industrial doctorate, fellowship, bursary, subsidy, "
        "financement, Förderung, Förderprogramm, finanziamento, financiamento, "
        "beca de investigación, stipendium, anslag, research grant, EU funding, "
        "Horizon, Marie Curie, innovation fund"
    ),
    "hackathon": (
        "hackathon, hack, coding sprint, innovation sprint, makeathon, datathon, "
        "buildathon, 24-hour, 48-hour, bootcamp, sprint event, coding event, "
        "hackatón, Hackathon, marathone de programmation, maratona di coding"
    ),
    "lab": (
        "lab, laboratory, research lab, research facility, equipment access, "
        "infrastructure, competence centre, EduSpace, makerspace, fab lab, fablab, "
        "clean room, testing facility, shared facility, research infrastructure, "
        "laboratorio, Laboratorium, laboratoire, laboratório, laboratorium, "
        "laboratorija, labb"
    ),
    "project_opportunity": (
        "project, research project, innovation project, collaboration project, "
        "R&D project, joint research, open project, project invitation, "
        "research partner, industry project, applied project, student project, "
        "progetto, Projekt, projet, projeto, projecto, prosjekt, projekt"
    ),
    "research_group": (
        "research group, research team, research unit, department, specialization, "
        "competence area, research area, group profile, team profile, "
        "research community, academic group, research centre, "
        "gruppo di ricerca, Forschungsgruppe, groupe de recherche, "
        "grupo de investigación, forskningsgrupp, pesquisadores"
    ),
    "service": (
        "service, consulting, advisory, business support, professional service, "
        "patent, licensing, IP management, intellectual property, "
        "technology transfer, TTO, legal support, innovation service, "
        "servizio, Dienstleistung, service professionnel, serviço, "
        "servicio, tjänst, valorisation"
    ),
    "testbed": (
        "testbed, test bed, testing environment, validation, pilot, "
        "proof of concept, PoC, prototype testing, demonstration, "
        "industrial testing, product validation, technology demonstration, "
        "banc de test, Testumgebung, banco di prova, banco de testes, "
        "provbed, living lab"
    ),
    "training": (
        "training, course, programme, program, degree, master, bachelor, "
        "PhD, doctorate, doctoral, executive education, ECTS, credits, "
        "qualification, certificate, diploma, curriculum, learning, education, "
        "exchange, Erasmus, semester abroad, study abroad, mobility, "
        "formation, Ausbildung, Studiengang, formazione, formação, "
        "programa educativo, utbildning, koulutus, opleiding"
    ),
}


def seed_all_keywords(apps, schema_editor):
    OfferType = apps.get_model("content", "OfferType")
    for name, keywords in _KEYWORDS.items():
        updated = OfferType.objects.filter(name=name, keywords="").update(keywords=keywords)
        if updated == 0:
            # Non-empty or not found — skip to avoid overwriting manual edits
            pass


class Migration(migrations.Migration):
    dependencies = [("content", "0020_offertype_keywords_english")]
    operations = [migrations.RunPython(seed_all_keywords, migrations.RunPython.noop)]
