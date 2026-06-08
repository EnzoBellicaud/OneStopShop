from django.core.management.base import BaseCommand
from django.db import transaction

from content.auth import hash_password
from content.models import (
    AllowedDomain,
    ContactRole,
    Domain,
    OfferType,
    Organization,
    ScrapingSource,
    SourceType,
    TargetProfile,
    User,
    UserOrganization,
    UserRole,
)
from content.seeding import load_task2_seed, uuid_from_token


class Command(BaseCommand):
    help = "Seeds lookup/reference tables and foundational organizations/users."

    @transaction.atomic
    def handle(self, *args, **options):
        data = load_task2_seed()

        for row in data["offer_types"]:
            OfferType.objects.update_or_create(
                id=uuid_from_token(row["id"].strip("{}")),
                defaults={"name": row["name"], "description": row["description"]},
            )

        _OFFER_TYPE_KEYWORDS = {
            "internship": (
                "internship, intern, placement, work experience, traineeship, "
                "stage, praktik, tirocinio, estágio, Praktikum, stagiaire, pratica"
            ),
            "thesis": (
                "thesis, dissertation, final project, capstone, research project, "
                "master thesis, bachelor thesis, "
                "examensarbete, abschlussarbeit, mémoire, tesi di laurea, "
                "trabalho de conclusão, doktorarbeit"
            ),
            "scholarship": (
                "scholarship, grant, fellowship, bursary, financial aid, funding, "
                "stipendium, bourse, borsa di studio, bolsa, stipendio, beca, studienbörse"
            ),
            "job": (
                "job, position, vacancy, employment, career, full-time, part-time, hiring, "
                "emploi, stelle, lavoro, emprego, jobb, arbeit, offre d emploi"
            ),
            "course": (
                "course, class, training, programme, program, workshop, seminar, lecture, "
                "kurs, cours, corso, kurso, opleiding, formation, ausbildung"
            ),
            "exchange": (
                "exchange, mobility, abroad, semester abroad, study abroad, "
                "échange, scambio, intercâmbio, Austausch, utbyte, erasmus"
            ),
            "challenge": (
                "challenge, open challenge, open call, call for solutions, competition, "
                "contest, prize, problem-solving, open innovation, "
                "defi, Herausforderung, sfida, desafio, tävling, Wettbewerb, "
                "concours, concorso, competição, gara"
            ),
            "co_creation": (
                "co-creation, co creation, collaboration, partnership, joint project, "
                "co-design, innovation partnership, spin-off, joint venture, consortium, "
                "collaborazione, samarbete, zusammenarbeit, coopération, parceria, "
                "colaboración, samenwerking, coinnovation"
            ),
            "funding_partner": (
                "funding, grant, financial support, research funding, call for proposals, "
                "doctoral funding, fellowship, bursary, subsidy, "
                "financement, Förderung, Förderprogramm, finanziamento, financiamento, "
                "beca de investigación, stipendium, anslag, research grant, "
                "EU funding, Horizon, Marie Curie, innovation fund"
            ),
            "hackathon": (
                "hackathon, hack, coding sprint, innovation sprint, makeathon, datathon, "
                "buildathon, bootcamp, sprint event, coding event, "
                "hackatón, marathone de programmation, maratona di coding"
            ),
            "lab": (
                "lab, laboratory, research lab, research facility, equipment access, "
                "infrastructure, competence centre, makerspace, fab lab, fablab, "
                "clean room, testing facility, shared facility, research infrastructure, "
                "laboratorio, Laboratorium, laboratoire, laboratório, labb"
            ),
            "project_opportunity": (
                "project, research project, innovation project, collaboration project, "
                "R&D project, joint research, open project, project invitation, "
                "research partner, industry project, applied project, student project, "
                "progetto, Projekt, projet, projeto, projecto, prosjekt"
            ),
            "research_group": (
                "research group, research team, research unit, department, specialization, "
                "competence area, research area, group profile, research community, "
                "academic group, research centre, "
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
                "programa educativo, utbildning, opleiding"
            ),
        }
        for name, keywords in _OFFER_TYPE_KEYWORDS.items():
            OfferType.objects.filter(name=name, keywords="").update(keywords=keywords)

        for row in data["domains"]:
            Domain.objects.update_or_create(
                id=uuid_from_token(row["id"].strip("{}")),
                defaults={"name": row["name"]},
            )

        for row in data["target_profiles"]:
            TargetProfile.objects.update_or_create(
                id=uuid_from_token(row["id"].strip("{}")),
                defaults={"name": row["name"], "description": row["description"]},
            )

        for row in data["source_types"]:
            SourceType.objects.update_or_create(
                id=uuid_from_token(row["id"].strip("{}")),
                defaults={"name": row["name"], "description": row["description"]},
            )

        for row in data["user_roles"]:
            UserRole.objects.update_or_create(
                id=uuid_from_token(row["id"].strip("{}")),
                defaults={"name": row["name"], "description": row["description"]},
            )

        for row in data["contact_roles"]:
            ContactRole.objects.update_or_create(
                id=uuid_from_token(row["value"]),
                defaults={"value": row["value"], "description": row["description"]},
            )

        organizations = [
            {
                "token": "unibz",
                "name": "Free University of Bozen-Bolzano (UNIBZ)",
                "country": "IT",
                "website": "https://www.unibz.it/en/",
            },
            {
                "token": "mdu",
                "name": "Malardalen University (MDU)",
                "country": "SE",
                "website": "https://www.mdu.se/en/malardalen-university",
            },
            {
                "token": "tu_ilmenau",
                "name": "TU Ilmenau",
                "country": "DE",
                "website": "https://www.tu-ilmenau.de/",
            },
            {
                "token": "uitm",
                "name": "University of Information Technology and Management (UITM)",
                "country": "PL",
                "website": "https://www.uitm.edu.eu/",
            },
            {
                "token": "utc",
                "name": "Université de Technologie de Compiègne (UTC)",
                "country": "FR",
                "website": "https://www.utc.fr/",
            },
            {
                "token": "euc",
                "name": "European University Cyprus (EUC)",
                "country": "CY",
                "website": "https://www.euc.ac.cy/",
            },
            {
                "token": "univpm",
                "name": "Università Politecnica delle Marche (UNIVPM)",
                "country": "IT",
                "website": "https://www.univpm.it/",
            },
            {
                "token": "unmo",
                "name": "University of Mostar (UNMO)",
                "country": "BA",
                "website": "https://www.unmo.ba/",
            },
            {
                "token": "ipvc",
                "name": "Instituto Politécnico de Viana do Castelo (IPVC)",
                "country": "PT",
                "website": "https://www.ipvc.pt/",
            },
            {
                "token": "demo_university",
                "name": "Demo University",
                "country": "IT",
                "website": "http://api:8000/mock/",
            },
        ]

        organization_map = {}
        for row in organizations:
            org, _ = Organization.objects.update_or_create(
                id=uuid_from_token(row["token"]),
                defaults={
                    "name": row["name"],
                    "type": Organization.OrganizationType.UNIVERSITY,
                    "country": row["country"],
                    "website": row["website"],
                },
            )
            organization_map[row["token"]] = org

        ScrapingSource.objects.update_or_create(
            key="demo_mock",
            defaults={
                "name": "Demo University",
                "url": "http://api:8000/mock/",
                "organization_token": "demo_university",
                "organization": organization_map.get("demo_university"),
                "target_profile": "student",
                "country": "IT",
                "quality": "mock",
                "llm_fallback_enabled": False,
                "enabled": True,
                "crawl_depth": 1,
                "crawl_max_pages": 50,
                "crawl_match_patterns": ["/mock/offers/"],
                "crawl_exclude_patterns": [],
            },
        )

        # Single shared password for all loginable seeded users
        SEED_PASSWORD = "passw0rd"

        users = [
            {
                "token": "user_ingestion_bot",
                "username": "ingestion_bot",
                "email": "ingestion-bot@oss.local",
                "profile": User.ProfileType.STUDENT,
                "loginable": False,
            },
            {
                "token": "user_admin_unibz",
                "username": "admin_unibz",
                "email": "admin-unibz@oss.local",
                "org_token": "unibz",
                "profile": User.ProfileType.TEACHER,
                "loginable": True,
            },
            {
                "token": "user_admin_mdu",
                "username": "admin_mdu",
                "email": "admin-mdu@oss.local",
                "org_token": "mdu",
                "profile": User.ProfileType.TEACHER,
                "loginable": True,
            },
        ]

        admin_role = UserRole.objects.get(name="admin")
        for row in users:
            loginable = row.get("loginable", False)
            user, _ = User.objects.update_or_create(
                id=uuid_from_token(row["token"]),
                defaults={
                    "username": row["username"],
                    "email": row["email"],
                    "password_hash": hash_password(SEED_PASSWORD) if loginable else "seeded-not-for-auth",
                    "profile": row["profile"],
                    "is_active": loginable,
                    "approval_status": User.ApprovalStatus.APPROVED if loginable else User.ApprovalStatus.PENDING,
                    "email_verified": loginable,
                },
            )

            if "org_token" in row:
                UserOrganization.objects.update_or_create(
                    user=user,
                    organization=organization_map[row["org_token"]],
                    role=admin_role,
                )

        # Seeded admin user (idempotent — credentials: admin / passw0rd)
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@sunrise-oss.local",
                "password_hash": hash_password("passw0rd"),
                "profile": User.ProfileType.ADMIN,
                "is_active": True,
                "approval_status": User.ApprovalStatus.APPROVED,
                "email_verified": True,
            },
        )
        if not created:
            # Ensure existing admin has correct profile/status regardless of prior state
            update_fields = []
            if admin_user.profile != User.ProfileType.ADMIN:
                admin_user.profile = User.ProfileType.ADMIN
                update_fields.append("profile")
            if not admin_user.is_active:
                admin_user.is_active = True
                update_fields.append("is_active")
            if admin_user.approval_status != User.ApprovalStatus.APPROVED:
                admin_user.approval_status = User.ApprovalStatus.APPROVED
                update_fields.append("approval_status")
            if update_fields:
                admin_user.save(update_fields=update_fields)

        # AllowedDomain seeds (teacher email domain whitelist)
        allowed_domain_seeds = [
            ("unibz.it", "unibz"),
            ("mdu.se", "mdu"),
            ("tu-ilmenau.de", "tu_ilmenau"),
            ("utc.fr", "utc"),
            ("euc.ac.cy", "euc"),
            ("uitm.edu.my", "uitm"),
            ("univpm.it", "univpm"),
            ("unmo.ac.me", "unmo"),
            ("ipvc.pt", "ipvc"),
        ]
        for domain_str, org_token in allowed_domain_seeds:
            org = organization_map.get(org_token)
            if org:
                AllowedDomain.objects.get_or_create(
                    domain=domain_str,
                    defaults={"organization": org, "description": f"Staff email domain for {org.name}"},
                )

        # Remove deprecated types. Safe: scraper no longer assigns these;
        # Offer FK is PROTECT so deletion will surface any orphaned offers
        # that need manual reclassification rather than silently losing data.
        removed_types = OfferType.objects.filter(
            name__in=["mobility", "expertise", "event"]
        )
        for ot in removed_types:
            orphans = ot.offers.count()
            if orphans:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping removal of offer_type '{ot.name}' — {orphans} offer(s) still reference it. Reclassify first."
                    )
                )
            else:
                ot.delete()
                self.stdout.write(f"  Removed deprecated offer_type: {ot.name}")

        removed_domains = Domain.objects.filter(
            name__in=["Multilingualism", "Industry_collaboration"]
        )
        for dom in removed_domains:
            dom.delete()
            self.stdout.write(f"  Removed deprecated domain: {dom.name}")

        self.stdout.write(self.style.SUCCESS("Lookup and foundational seed completed."))
