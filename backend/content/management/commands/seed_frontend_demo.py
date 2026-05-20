from django.core.management.base import BaseCommand

from content.auth import hash_password
from content.matching_service import run_matching_for_offers
from content.models import (
    Domain,
    Offer,
    OfferType,
    Organization,
    SourceType,
    TargetProfile,
    User,
    UserFavorite,
    UserNeed,
    UserProfile,
)


class Command(BaseCommand):
    help = "Seeds demo dashboard data for local frontend testing."

    def handle(self, *args, **options):
        password = "DemoPassword123"
        user, _ = User.objects.update_or_create(
            username="frontend_demo",
            defaults={
                "email": "frontend.demo@example.com",
                "password_hash": hash_password(password),
                "first_name": "Frontend",
                "last_name": "Demo",
                "profile": User.ProfileType.STUDENT,
                "is_active": True,
            },
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "bio": "Demo account for testing the dashboard and matching flow.",
                "preferred_domains": ["AI", "Data Science"],
                "preferred_countries": ["IT", "DE", "NL"],
                "notification_enabled": True,
            },
        )

        target_student, _ = TargetProfile.objects.get_or_create(
            name="student",
            defaults={"description": "Student learner profile"},
        )
        offer_type, _ = OfferType.objects.get_or_create(
            name="course",
            defaults={"description": "Course or training opportunity"},
        )
        source_type, _ = SourceType.objects.get_or_create(
            name="manual",
            defaults={"description": "Manual/demo content"},
        )
        organization, _ = Organization.objects.update_or_create(
            name="Demo Tech University",
            defaults={
                "type": Organization.OrganizationType.UNIVERSITY,
                "country": "IT",
                "website": "https://demo-tech.example.edu",
            },
        )

        domain_ai, _ = Domain.objects.get_or_create(name="AI")
        domain_data, _ = Domain.objects.get_or_create(name="Data Science")
        domain_robotics, _ = Domain.objects.get_or_create(name="Robotics")

        needs = [
            {
                "title": "Python data science and machine learning",
                "description": "Looking for a practical AI course with Python, data analysis, and machine learning.",
                "countries": ["IT", "DE", "NL"],
                "domains": [domain_ai, domain_data],
            },
            {
                "title": "Robotics prototyping support",
                "description": "Need hands-on robotics labs, sensors, embedded systems, and prototype mentoring.",
                "countries": ["IT", "NL"],
                "domains": [domain_robotics, domain_ai],
            },
        ]
        seeded_needs = []
        for item in needs:
            need, _ = UserNeed.objects.update_or_create(
                user=user,
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "target_profile": target_student,
                    "status": UserNeed.NeedStatus.ACTIVE,
                    "countries": item["countries"],
                },
            )
            need.domains.set(item["domains"])
            seeded_needs.append(need)

        offer_rows = [
            {
                "title": "Python Data Science and Machine Learning Bootcamp",
                "summary": "A practical Python bootcamp covering data science, AI, machine learning, and portfolio projects.",
                "link": "https://demo-tech.example.edu/offers/python-data-science",
                "country": "IT",
                "domains": [domain_ai, domain_data],
            },
            {
                "title": "Robotics AI Prototype Lab",
                "summary": "Build robotics prototypes with sensors, embedded systems, computer vision, and AI mentoring.",
                "link": "https://demo-tech.example.edu/offers/robotics-ai-lab",
                "country": "NL",
                "domains": [domain_robotics, domain_ai],
            },
            {
                "title": "Applied Data Analytics Microcredential",
                "summary": "Short data analytics course focused on Python, dashboards, and applied machine learning workflows.",
                "link": "https://demo-tech.example.edu/offers/applied-data-analytics",
                "country": "DE",
                "domains": [domain_data],
            },
        ]
        offers = []
        for row in offer_rows:
            offer, _ = Offer.objects.update_or_create(
                link=row["link"],
                defaults={
                    "title": row["title"],
                    "summary": row["summary"],
                    "country": row["country"],
                    "details": {"demo": True},
                    "status": Offer.OfferStatus.PUBLISHED,
                    "source_type": source_type,
                    "target_profile": target_student,
                    "organization": organization,
                    "created_by": user,
                    "updated_by": user,
                    "offer_type": offer_type,
                },
            )
            offer.domains.set(row["domains"])
            offers.append(offer)

        UserFavorite.objects.update_or_create(
            user=user,
            offer=offers[0],
            defaults={"note": "Good first option for frontend dashboard testing."},
        )

        stats = run_matching_for_offers([offer.id for offer in offers])

        self.stdout.write(self.style.SUCCESS("Frontend demo data seeded."))
        self.stdout.write(f"Login username: frontend_demo")
        self.stdout.write(f"Login password: {password}")
        self.stdout.write(f"Needs: {len(seeded_needs)}")
        self.stdout.write(f"Offers: {len(offers)}")
        self.stdout.write(f"Matching stats: {stats}")
