from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import Domain, Offer, OfferDomain, OfferType, Organization, SourceType, TargetProfile, User
from content.seeding import uuid_from_token

OFFERS = [
    # ── STUDENT — Internship ─────────────────────────────────────────────────
    {
        "token": "offer_internship_ai_unibz",
        "title": "AI Research Internship – Computer Vision Lab",
        "summary": (
            "Join UNIBZ's Computer Vision Lab for a 3-month paid internship. "
            "Work alongside PhD researchers on deep-learning models for autonomous systems. "
            "Ideal for BSc/MSc students in Computer Science or Electrical Engineering."
        ),
        "link": "https://www.unibz.it/en/faculties/engineering/research/computer-vision/internship/",
        "country": "IT",
        "offer_type": "internship",
        "target_profile": "student",
        "org_token": "unibz",
        "domains": ["AI", "Robotics"],
    },
    {
        "token": "offer_internship_cyber_mdu",
        "title": "Cybersecurity Internship – MDU Security Research Group",
        "summary": (
            "MDU offers a 6-month internship in its Cybersecurity Research Group. "
            "Tasks include vulnerability analysis, penetration testing, and writing research reports. "
            "Open to students in their final year of a relevant programme."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/research-groups/cybersecurity-internship",
        "country": "SE",
        "offer_type": "internship",
        "target_profile": "student",
        "org_token": "mdu",
        "domains": ["Cybersecurity", "Digitalisation"],
    },
    {
        "token": "offer_internship_sustain_utc",
        "title": "Sustainability Engineering Internship",
        "summary": (
            "UTC invites students to a 4-month internship focused on sustainable manufacturing processes. "
            "You will contribute to real industry projects alongside academic mentors and company partners."
        ),
        "link": "https://www.utc.fr/en/studying-at-utc/internships/sustainability-engineering/",
        "country": "FR",
        "offer_type": "internship",
        "target_profile": "student",
        "org_token": "utc",
        "domains": ["Sustainability", "Innovation_and_entrepreneurship"],
    },
    # ── STUDENT — Thesis ─────────────────────────────────────────────────────
    {
        "token": "offer_thesis_robotics_unibz",
        "title": "MSc Thesis – Collaborative Robotics in Smart Factories",
        "summary": (
            "UNIBZ offers supervised MSc thesis positions within the Robotics & Automation group. "
            "Topics include human-robot collaboration, sensor fusion, and real-time control systems. "
            "Industry co-supervision available with NOI Techpark partners."
        ),
        "link": "https://www.unibz.it/en/faculties/engineering/research/robotics/thesis-topics/",
        "country": "IT",
        "offer_type": "thesis",
        "target_profile": "student",
        "org_token": "unibz",
        "domains": ["Robotics", "AI"],
    },
    {
        "token": "offer_thesis_digital_mdu",
        "title": "Bachelor/Master Thesis – Digital Transformation in SMEs",
        "summary": (
            "Investigate how small and medium enterprises adopt digital tools and what barriers they face. "
            "The thesis is co-supervised by MDU's Digitalisation research group and a regional industry partner."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/research-specialisations/digitalisation/thesis",
        "country": "SE",
        "offer_type": "thesis",
        "target_profile": "student",
        "org_token": "mdu",
        "domains": ["Digitalisation", "Regional_development"],
    },
    {
        "token": "offer_thesis_sustain_ipvc",
        "title": "Thesis – Circular Economy Strategies for Coastal Communities",
        "summary": (
            "IPVC invites students to develop a thesis on circular economy models adapted to coastal and rural regions. "
            "Field work in Viana do Castelo region included. Eligible for Erasmus+ research grant."
        ),
        "link": "https://www.ipvc.pt/en/research/thesis-opportunities/circular-economy",
        "country": "PT",
        "offer_type": "thesis",
        "target_profile": "student",
        "org_token": "ipvc",
        "domains": ["Sustainability", "Regional_development"],
    },
    # ── STUDENT — Challenge ───────────────────────────────────────────────────
    {
        "token": "offer_challenge_ai_tu_ilmenau",
        "title": "AI Innovation Challenge – Smart City Solutions",
        "summary": (
            "TU Ilmenau and city partners challenge student teams to design AI-powered solutions "
            "for urban mobility, energy management, or public safety. "
            "Top teams receive €5 000 in prize money and an industry mentoring programme."
        ),
        "link": "https://www.tu-ilmenau.de/en/university/events/ai-innovation-challenge/",
        "country": "DE",
        "offer_type": "challenge",
        "target_profile": "student",
        "org_token": "tu_ilmenau",
        "domains": ["AI", "Digitalisation"],
    },
    {
        "token": "offer_challenge_sustain_euc",
        "title": "Green Campus Challenge – Sustainable Campus Redesign",
        "summary": (
            "European University Cyprus invites students across all disciplines to propose "
            "innovative ideas for reducing the carbon footprint of university campuses. "
            "Winning proposals will be implemented in partnership with local authorities."
        ),
        "link": "https://www.euc.ac.cy/en/campus-life/sustainability/green-campus-challenge/",
        "country": "CY",
        "offer_type": "challenge",
        "target_profile": "student",
        "org_token": "euc",
        "domains": ["Sustainability", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_challenge_cyber_uitm",
        "title": "CyberDefend Student Competition",
        "summary": (
            "UITM's annual cybersecurity competition challenges students to defend simulated "
            "infrastructure against real attack scenarios. Compete individually or in teams of up to 4. "
            "Winners earn internship offers at partner security firms."
        ),
        "link": "https://www.uitm.edu.eu/en/research/cybersecurity/cyberdefend-competition",
        "country": "PL",
        "offer_type": "challenge",
        "target_profile": "student",
        "org_token": "uitm",
        "domains": ["Cybersecurity", "Digitalisation"],
    },
    # ── STUDENT — Hackathon ───────────────────────────────────────────────────
    {
        "token": "offer_hackathon_ai_univpm",
        "title": "48h AI Hackathon – Healthcare Data",
        "summary": (
            "UNIVPM hosts a 48-hour hackathon where multidisciplinary teams build AI prototypes "
            "using real anonymised healthcare datasets provided by regional hospitals. "
            "Mentoring from faculty and industry experts throughout the event."
        ),
        "link": "https://www.univpm.it/Entra/Engine/RAServePG.php/P/25251IT2601010/T/Hackathon-AI-Healthcare",
        "country": "IT",
        "offer_type": "hackathon",
        "target_profile": "student",
        "org_token": "univpm",
        "domains": ["AI", "Digitalisation"],
    },
    {
        "token": "offer_hackathon_sustain_mdu",
        "title": "Green Hack – Climate Tech Weekend",
        "summary": (
            "Join MDU's 36-hour sustainability hackathon. Teams tackle climate challenges "
            "using IoT sensors, data analytics, and circular design thinking. "
            "Open to all students — no prior coding experience required for non-technical tracks."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/events/green-hack",
        "country": "SE",
        "offer_type": "hackathon",
        "target_profile": "student",
        "org_token": "mdu",
        "domains": ["Sustainability", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_hackathon_digital_unmo",
        "title": "DigiHack – Digitalisation for Public Services",
        "summary": (
            "University of Mostar organises DigiHack, a student hackathon focused on digitising "
            "local government services in the Western Balkans. "
            "Winning solutions are piloted by the Mostar City administration."
        ),
        "link": "https://www.unmo.ba/en/digihack",
        "country": "BA",
        "offer_type": "hackathon",
        "target_profile": "student",
        "org_token": "unmo",
        "domains": ["Digitalisation", "Regional_development"],
    },
    # ── STUDENT — Mobility (domain filter) ───────────────────────────────────
    {
        "token": "offer_training_mobility_unibz",
        "title": "Erasmus+ Student Exchange – Engineering & Technology",
        "summary": (
            "UNIBZ participates in the Erasmus+ programme, offering student exchange places "
            "in partner universities across Europe. Study abroad for one or two semesters "
            "while earning credits recognised by your home institution."
        ),
        "link": "https://www.unibz.it/en/services/erasmus-exchange/students-outgoing/",
        "country": "IT",
        "offer_type": "training",
        "target_profile": "student",
        "org_token": "unibz",
        "domains": ["Mobility", "STEAM_education"],
    },
    {
        "token": "offer_training_mobility_mdu",
        "title": "International Exchange Programme – MDU Outgoing Students",
        "summary": (
            "MDU has exchange agreements with 150+ universities worldwide. "
            "Students can spend one semester abroad with full academic credit transfer. "
            "Scholarships are available through the Swedish Institute and Erasmus+."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/education/exchange-studies/outgoing",
        "country": "SE",
        "offer_type": "training",
        "target_profile": "student",
        "org_token": "mdu",
        "domains": ["Mobility", "Digitalisation"],
    },
    # ── RESEARCHER — Research Group ───────────────────────────────────────────
    {
        "token": "offer_research_group_ai_unibz",
        "title": "UNIBZ – IDSE Research Group: Intelligent & Distributed Systems",
        "summary": (
            "The IDSE group at UNIBZ conducts research in AI, distributed computing, and data engineering. "
            "Open to collaboration with industry partners and visiting researchers. "
            "Active EU-funded projects include Horizon Europe and INTERREG initiatives."
        ),
        "link": "https://www.unibz.it/en/faculties/engineering/research/idse/",
        "country": "IT",
        "offer_type": "research_group",
        "target_profile": "researcher",
        "org_token": "unibz",
        "domains": ["AI", "Digitalisation"],
    },
    {
        "token": "offer_research_group_robotics_mdu",
        "title": "MDU – Robotics & Autonomous Systems Research Specialisation",
        "summary": (
            "MDU's Robotics group works on autonomous vehicles, industrial automation, and embedded systems. "
            "Collaborating partners include Volvo, ABB, and the Swedish Defence Research Agency (FOI). "
            "Open calls for postdoc and visiting researcher positions are published annually."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/research-specialisations/robotics-and-autonomous-systems",
        "country": "SE",
        "offer_type": "research_group",
        "target_profile": "researcher",
        "org_token": "mdu",
        "domains": ["Robotics", "AI"],
    },
    {
        "token": "offer_research_group_sustain_utc",
        "title": "UTC – COSTECH Lab: Knowledge, Technology & Society",
        "summary": (
            "COSTECH at UTC bridges engineering, social sciences, and humanities to study "
            "sustainable development and technology transitions. "
            "Welcomes postdoctoral researchers and PhD candidates with interdisciplinary profiles."
        ),
        "link": "https://www.utc.fr/en/research/research-labs/costech/",
        "country": "FR",
        "offer_type": "research_group",
        "target_profile": "researcher",
        "org_token": "utc",
        "domains": ["Sustainability", "Social_transformation"],
    },
    # ── RESEARCHER — Funding Partner ──────────────────────────────────────────
    {
        "token": "offer_funding_partner_ai_tu_ilmenau",
        "title": "Joint Research Funding – AI & Embedded Systems (TU Ilmenau + Industry)",
        "summary": (
            "TU Ilmenau invites industry partners to co-fund applied research projects in "
            "AI-driven embedded systems. Partners gain IP co-ownership, access to lab infrastructure, "
            "and priority hiring from the talent pipeline."
        ),
        "link": "https://www.tu-ilmenau.de/en/university/transfer/research-cooperation/funding-calls/",
        "country": "DE",
        "offer_type": "funding_partner",
        "target_profile": "researcher",
        "org_token": "tu_ilmenau",
        "domains": ["AI", "Technology_transfer"],
    },
    {
        "token": "offer_funding_partner_innov_ipvc",
        "title": "IPVC Innovation Fund – Calls for Research Partnership Proposals",
        "summary": (
            "IPVC opens biannual calls for SMEs and startups to co-develop applied research projects "
            "with university researchers. Funding covers up to 70% of project costs via national and EU instruments."
        ),
        "link": "https://www.ipvc.pt/en/research/funding-partnerships/",
        "country": "PT",
        "offer_type": "funding_partner",
        "target_profile": "researcher",
        "org_token": "ipvc",
        "domains": ["Innovation_and_entrepreneurship", "Regional_development"],
    },
    # ── COMPANY — Funding Partner ─────────────────────────────────────────────
    {
        "token": "offer_funding_partner_company_univpm",
        "title": "UNIVPM – Technology Transfer & Co-Funding for Companies",
        "summary": (
            "UNIVPM's TTO connects companies with researchers for co-funded R&D projects. "
            "SMEs can access national and EU grants with university support for proposal writing, "
            "project management, and IP protection."
        ),
        "link": "https://www.univpm.it/Entra/Engine/RAServePG.php/P/25251IT2601010/T/TTO-Company-Funding",
        "country": "IT",
        "offer_type": "funding_partner",
        "target_profile": "company",
        "org_token": "univpm",
        "domains": ["Technology_transfer", "Innovation_and_entrepreneurship"],
    },
    # ── COMPANY — Research Group ──────────────────────────────────────────────
    {
        "token": "offer_research_group_company_uitm",
        "title": "UITM – Cybersecurity Lab: Industry Partnership Programme",
        "summary": (
            "UITM's Cybersecurity Lab offers companies access to specialised testing environments, "
            "expert consultancy, and joint R&D on security protocols. "
            "Partnership packages include dedicated lab time and co-authored publications."
        ),
        "link": "https://www.uitm.edu.eu/en/research/cybersecurity/industry-partnership",
        "country": "PL",
        "offer_type": "research_group",
        "target_profile": "company",
        "org_token": "uitm",
        "domains": ["Cybersecurity", "Technology_transfer"],
    },

    # ── RESEARCHER — Testbed (Infrastructure) ────────────────────────────────
    {
        "token": "offer_testbed_iot_unibz",
        "title": "UNIBZ IoT & Edge Computing Testbed – Open Access for Researchers",
        "summary": (
            "UNIBZ provides shared access to its IoT and edge computing testbed infrastructure, "
            "including sensor networks, edge nodes, and a private 5G slice. "
            "Academic researchers can apply for allocated time slots to run experiments."
        ),
        "link": "https://www.unibz.it/en/faculties/engineering/research/infrastructure/iot-testbed/",
        "country": "IT",
        "offer_type": "testbed",
        "target_profile": "researcher",
        "org_token": "unibz",
        "domains": ["AI", "Digitalisation"],
    },
    {
        "token": "offer_testbed_robotics_mdu",
        "title": "MDU Robotics & Autonomous Systems Testbed",
        "summary": (
            "MDU's robotics testbed hosts industrial robot arms, mobile platforms, and "
            "a VICON motion-capture system. Available to academic collaborators for experiments "
            "in human-robot interaction, path planning, and embedded control."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/infrastructure/robotics-testbed",
        "country": "SE",
        "offer_type": "testbed",
        "target_profile": "researcher",
        "org_token": "mdu",
        "domains": ["Robotics", "AI"],
    },
    {
        "token": "offer_testbed_embedded_tu_ilmenau",
        "title": "TU Ilmenau – Embedded Systems & RF Testbed Infrastructure",
        "summary": (
            "TU Ilmenau's testbed covers hardware-in-the-loop simulation, RF signal testing, "
            "and real-time embedded systems evaluation. "
            "Open to visiting researchers and EU project partners under shared usage agreements."
        ),
        "link": "https://www.tu-ilmenau.de/en/university/facilities/embedded-systems-testbed/",
        "country": "DE",
        "offer_type": "testbed",
        "target_profile": "researcher",
        "org_token": "tu_ilmenau",
        "domains": ["Digitalisation", "Technology_transfer"],
    },

    # ── RESEARCHER — Service (Experts) ────────────────────────────────────────
    {
        "token": "offer_service_innovation_utc",
        "title": "UTC – Innovation & Technology Transfer Expert Advisory",
        "summary": (
            "UTC's transfer office provides researchers with expert guidance on IP protection, "
            "spin-off creation, and commercialisation strategies. "
            "One-to-one advisory sessions and group workshops are available on request."
        ),
        "link": "https://www.utc.fr/en/research/technology-transfer/advisory-services/",
        "country": "FR",
        "offer_type": "service",
        "target_profile": "researcher",
        "org_token": "utc",
        "domains": ["Innovation_and_entrepreneurship", "Technology_transfer"],
    },
    {
        "token": "offer_service_cyber_uitm",
        "title": "UITM – Cybersecurity Expert Consultancy for Research Projects",
        "summary": (
            "UITM's security specialists offer audit, threat modelling, and penetration-testing services "
            "to research teams building digital systems. "
            "Packages range from a half-day review to a full security assessment report."
        ),
        "link": "https://www.uitm.edu.eu/en/research/cybersecurity/expert-services",
        "country": "PL",
        "offer_type": "service",
        "target_profile": "researcher",
        "org_token": "uitm",
        "domains": ["Cybersecurity", "Digitalisation"],
    },
    {
        "token": "offer_service_data_univpm",
        "title": "UNIVPM – Data Science & Statistical Analysis Expert Services",
        "summary": (
            "UNIVPM's data science team offers statistical consulting, dataset preparation, "
            "and machine-learning model validation services to external research projects. "
            "Services are available under a memorandum of collaboration or a fee-for-service contract."
        ),
        "link": "https://www.univpm.it/Entra/Engine/RAServePG.php/P/25251IT2601010/T/Data-Science-Services",
        "country": "IT",
        "offer_type": "service",
        "target_profile": "researcher",
        "org_token": "univpm",
        "domains": ["AI", "Technology_transfer"],
    },

    # ── RESEARCHER — Co-creation (Demonstrators) ──────────────────────────────
    {
        "token": "offer_cocreation_living_lab_unibz",
        "title": "UNIBZ Living Lab – Co-creation & Field Demonstration Platform",
        "summary": (
            "The UNIBZ Living Lab provides a real-world environment for co-creating and demonstrating "
            "digital solutions with end users, local SMEs, and public institutions. "
            "Researchers can run prototype demonstrations and collect user feedback in situ."
        ),
        "link": "https://www.unibz.it/en/faculties/engineering/research/living-lab/",
        "country": "IT",
        "offer_type": "co_creation",
        "target_profile": "researcher",
        "org_token": "unibz",
        "domains": ["Co_creation_and_testbeds", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_cocreation_industry_mdu",
        "title": "MDU – Industry Co-creation Demonstrator Programme",
        "summary": (
            "MDU connects researchers with regional industry partners to co-develop and demonstrate "
            "proof-of-concept solutions. The programme covers three months of joint sprints, "
            "culminating in a public demonstration event attended by investors and policymakers."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/co-creation/industry-demonstrators",
        "country": "SE",
        "offer_type": "co_creation",
        "target_profile": "researcher",
        "org_token": "mdu",
        "domains": ["Co_creation_and_testbeds", "Technology_transfer"],
    },
    {
        "token": "offer_cocreation_smart_euc",
        "title": "EUC – Smart Campus Co-creation & Demonstration Hub",
        "summary": (
            "European University Cyprus runs a smart-campus demonstrator where researchers "
            "can pilot sustainability, mobility, and digital-health solutions in a live environment. "
            "The hub hosts quarterly open-demonstration days for stakeholders."
        ),
        "link": "https://www.euc.ac.cy/en/research/smart-campus-hub/",
        "country": "CY",
        "offer_type": "co_creation",
        "target_profile": "researcher",
        "org_token": "euc",
        "domains": ["Co_creation_and_testbeds", "Sustainability"],
    },

    # ── RESEARCHER — Project Opportunity ──────────────────────────────────────
    {
        "token": "offer_project_horizon_unibz",
        "title": "UNIBZ – Open Call: Horizon Europe Partner Search (AI & Data)",
        "summary": (
            "UNIBZ is forming consortia for upcoming Horizon Europe calls in AI, data spaces, and "
            "trustworthy computing. Researchers from eligible countries are invited to express interest "
            "and contribute to proposal development."
        ),
        "link": "https://www.unibz.it/en/research/horizon-europe/partner-search/",
        "country": "IT",
        "offer_type": "project_opportunity",
        "target_profile": "researcher",
        "org_token": "unibz",
        "domains": ["AI", "Digitalisation"],
    },
    {
        "token": "offer_project_interreg_mdu",
        "title": "MDU – INTERREG Cross-Border Research Project: Sustainable Mobility",
        "summary": (
            "MDU seeks academic partners for an INTERREG Scandinavia–Baltic project on "
            "sustainable urban mobility solutions. The project covers electrification, "
            "shared mobility systems, and data-driven traffic management."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/projects/interreg-mobility",
        "country": "SE",
        "offer_type": "project_opportunity",
        "target_profile": "researcher",
        "org_token": "mdu",
        "domains": ["Mobility", "Sustainability"],
    },
    {
        "token": "offer_project_regional_ipvc",
        "title": "IPVC – Regional Innovation Project: Blue Economy & Coastal Tech",
        "summary": (
            "IPVC coordinates a regional innovation project focused on marine technologies, "
            "aquaculture automation, and coastal environmental monitoring. "
            "Partners from research and industry are invited to join the next project phase."
        ),
        "link": "https://www.ipvc.pt/en/research/projects/blue-economy/",
        "country": "PT",
        "offer_type": "project_opportunity",
        "target_profile": "researcher",
        "org_token": "ipvc",
        "domains": ["Sustainability", "Regional_development"],
    },

    # ── RESEARCHER — Training (Events) ────────────────────────────────────────
    {
        "token": "offer_training_methods_tu_ilmenau",
        "title": "TU Ilmenau – Advanced Research Methods Workshop Series",
        "summary": (
            "TU Ilmenau hosts a semester-long workshop series covering systematic literature review, "
            "experimental design, and research ethics. "
            "Open to doctoral students and postdoctoral researchers from partner institutions."
        ),
        "link": "https://www.tu-ilmenau.de/en/university/graduate-school/workshops/research-methods/",
        "country": "DE",
        "offer_type": "training",
        "target_profile": "researcher",
        "org_token": "tu_ilmenau",
        "domains": ["STEAM_education", "Social_transformation"],
    },
    {
        "token": "offer_training_doctoral_utc",
        "title": "UTC – Doctoral Training Event: Innovation & Valorisation",
        "summary": (
            "UTC organises an annual two-day doctoral training event on research valorisation, "
            "covering patent writing, startup creation, and academic-industry collaboration. "
            "Participants earn 1 ECTS credit recognized across Alliance partner universities."
        ),
        "link": "https://www.utc.fr/en/research/doctoral-school/training-events/",
        "country": "FR",
        "offer_type": "training",
        "target_profile": "researcher",
        "org_token": "utc",
        "domains": ["Innovation_and_entrepreneurship", "Technology_transfer"],
    },

    # ── COMPANY — Co-creation (Life Long Learning) ────────────────────────────
    {
        "token": "offer_cocreation_lll_unibz",
        "title": "UNIBZ – Executive Education & Lifelong Learning Programme",
        "summary": (
            "UNIBZ offers tailored lifelong learning programmes for working professionals in technology, "
            "management, and sustainability. Courses are co-created with industry partners to ensure "
            "immediate workplace applicability. Available in modular and micro-credential formats."
        ),
        "link": "https://www.unibz.it/en/services/lifelong-learning/",
        "country": "IT",
        "offer_type": "co_creation",
        "target_profile": "company",
        "org_token": "unibz",
        "domains": ["Innovation_and_entrepreneurship", "STEAM_education"],
    },
    {
        "token": "offer_cocreation_lll_mdu",
        "title": "MDU – Upskilling & Reskilling for Industry Professionals",
        "summary": (
            "MDU's lifelong learning unit co-designs short courses and micro-credentials with companies "
            "to address skill gaps in digitalisation, automation, and sustainable engineering. "
            "Programmes are delivered in blended format and can be customised per employer."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/education/lifelong-learning/",
        "country": "SE",
        "offer_type": "co_creation",
        "target_profile": "company",
        "org_token": "mdu",
        "domains": ["Digitalisation", "STEAM_education"],
    },
    {
        "token": "offer_cocreation_lll_utc",
        "title": "UTC – Continuing Education & Professional Development Programmes",
        "summary": (
            "UTC's continuing education division collaborates with companies to build bespoke "
            "training pathways for engineers and managers. Topics range from Industry 4.0 "
            "to sustainable innovation and project management."
        ),
        "link": "https://www.utc.fr/en/continuing-education/",
        "country": "FR",
        "offer_type": "co_creation",
        "target_profile": "company",
        "org_token": "utc",
        "domains": ["Innovation_and_entrepreneurship", "Social_transformation"],
    },

    # ── COMPANY — Service (Experts) ───────────────────────────────────────────
    {
        "token": "offer_service_cyber_company_uitm",
        "title": "UITM – Cybersecurity Expert Services for Enterprises",
        "summary": (
            "UITM's cybersecurity team delivers penetration testing, security audits, and "
            "compliance assessments (ISO 27001, NIS2) to private companies and public bodies. "
            "Rapid-response packages available for incident analysis."
        ),
        "link": "https://www.uitm.edu.eu/en/research/cybersecurity/enterprise-services",
        "country": "PL",
        "offer_type": "service",
        "target_profile": "company",
        "org_token": "uitm",
        "domains": ["Cybersecurity", "Technology_transfer"],
    },
    {
        "token": "offer_service_engineering_univpm",
        "title": "UNIVPM – Engineering Consultancy & Technical Expert Services",
        "summary": (
            "UNIVPM provides fee-for-service engineering consultancy covering structural analysis, "
            "materials testing, and mechatronics design review. "
            "Reports are delivered within agreed timelines and are legally certified."
        ),
        "link": "https://www.univpm.it/Entra/Engine/RAServePG.php/P/25251IT2601010/T/Engineering-Consultancy",
        "country": "IT",
        "offer_type": "service",
        "target_profile": "company",
        "org_token": "univpm",
        "domains": ["Technology_transfer", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_service_ai_company_tu_ilmenau",
        "title": "TU Ilmenau – AI & Data Analytics Expert Advisory for Companies",
        "summary": (
            "TU Ilmenau's AI faculty offers expert advisory services for companies implementing "
            "machine learning, computer vision, or predictive analytics. Services include "
            "feasibility studies, architecture review, and proof-of-concept development."
        ),
        "link": "https://www.tu-ilmenau.de/en/university/transfer/expert-services/ai-advisory/",
        "country": "DE",
        "offer_type": "service",
        "target_profile": "company",
        "org_token": "tu_ilmenau",
        "domains": ["AI", "Technology_transfer"],
    },

    # ── COMPANY — Training ────────────────────────────────────────────────────
    {
        "token": "offer_training_digital_company_mdu",
        "title": "MDU – Corporate Digital Transformation Training Programme",
        "summary": (
            "MDU delivers in-company and campus-based training on digital transformation strategies, "
            "agile methods, and data-driven decision-making. "
            "Programmes can be accredited as university micro-credentials."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/education/corporate-training/digital-transformation",
        "country": "SE",
        "offer_type": "training",
        "target_profile": "company",
        "org_token": "mdu",
        "domains": ["Digitalisation", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_training_sustain_company_utc",
        "title": "UTC – Corporate Sustainability & Green Engineering Training",
        "summary": (
            "UTC runs short intensive training courses for company teams on sustainable design, "
            "life-cycle assessment, and green manufacturing. "
            "On-site delivery available for groups of 10 or more participants."
        ),
        "link": "https://www.utc.fr/en/continuing-education/corporate-training/sustainability/",
        "country": "FR",
        "offer_type": "training",
        "target_profile": "company",
        "org_token": "utc",
        "domains": ["Sustainability", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_training_exec_company_unibz",
        "title": "UNIBZ – Executive Leadership & Innovation Management Training",
        "summary": (
            "UNIBZ's executive training unit offers leadership development programmes for senior "
            "managers, covering innovation management, cross-cultural teams, and tech strategy. "
            "Delivered in English and Italian; certificate of completion issued."
        ),
        "link": "https://www.unibz.it/en/services/executive-education/leadership-innovation/",
        "country": "IT",
        "offer_type": "training",
        "target_profile": "company",
        "org_token": "unibz",
        "domains": ["Innovation_and_entrepreneurship", "Social_transformation"],
    },

    # ── COMPANY — Testbed ─────────────────────────────────────────────────────
    {
        "token": "offer_testbed_iot_company_unibz",
        "title": "UNIBZ – IoT & Smart Systems Testbed Access for Companies",
        "summary": (
            "UNIBZ opens its IoT testbed infrastructure to companies for product validation, "
            "interoperability testing, and pre-certification trials. "
            "Flexible access packages from one-day trials to six-month long-term agreements."
        ),
        "link": "https://www.unibz.it/en/research/infrastructure/iot-testbed/industry-access/",
        "country": "IT",
        "offer_type": "testbed",
        "target_profile": "company",
        "org_token": "unibz",
        "domains": ["Co_creation_and_testbeds", "Digitalisation"],
    },
    {
        "token": "offer_testbed_embedded_company_tu_ilmenau",
        "title": "TU Ilmenau – Embedded Systems Testbed: Industry Validation Services",
        "summary": (
            "TU Ilmenau's embedded systems testbed offers companies hardware-in-the-loop testing, "
            "EMC pre-compliance screening, and real-time system benchmarking. "
            "ISO-compliant test reports provided for regulatory submissions."
        ),
        "link": "https://www.tu-ilmenau.de/en/university/transfer/testbed/embedded-systems/",
        "country": "DE",
        "offer_type": "testbed",
        "target_profile": "company",
        "org_token": "tu_ilmenau",
        "domains": ["Co_creation_and_testbeds", "Technology_transfer"],
    },
    {
        "token": "offer_testbed_autonomous_company_mdu",
        "title": "MDU – Autonomous Systems Testbed for Industrial Validation",
        "summary": (
            "MDU's autonomous systems testbed offers companies a safe environment to test "
            "autonomous vehicles, drones, and robotic systems. "
            "Access includes expert support, data logging, and a post-test analysis report."
        ),
        "link": "https://www.mdu.se/en/malardalen-university/research/infrastructure/autonomous-testbed/industry",
        "country": "SE",
        "offer_type": "testbed",
        "target_profile": "company",
        "org_token": "mdu",
        "domains": ["Co_creation_and_testbeds", "Robotics"],
    },

    # ── UNMO — Additional offers ──────────────────────────────────────────────
    {
        "token": "offer_research_group_unmo",
        "title": "UNMO – Digital Society Research Group: Western Balkans Focus",
        "summary": (
            "The University of Mostar's Digital Society research group studies digital transformation "
            "in emerging economies, with a focus on the Western Balkans region. "
            "Open to collaborative research projects and visiting scholars."
        ),
        "link": "https://www.unmo.ba/en/research/digital-society",
        "country": "BA",
        "offer_type": "research_group",
        "target_profile": "researcher",
        "org_token": "unmo",
        "domains": ["Digitalisation", "Regional_development"],
    },
    {
        "token": "offer_thesis_unmo",
        "title": "UNMO – Thesis Opportunity: Digital Infrastructure in Rural Communities",
        "summary": (
            "University of Mostar offers thesis positions investigating how rural communities in "
            "the Western Balkans adopt digital infrastructure. "
            "Field research in Herzegovina region included; Erasmus+ scholarship eligible."
        ),
        "link": "https://www.unmo.ba/en/studies/thesis-topics/digital-infrastructure",
        "country": "BA",
        "offer_type": "thesis",
        "target_profile": "student",
        "org_token": "unmo",
        "domains": ["Digitalisation", "Regional_development"],
    },
    {
        "token": "offer_training_company_unmo",
        "title": "UNMO – Digital Literacy Training for Local Enterprises",
        "summary": (
            "University of Mostar delivers practical digital literacy and e-commerce training "
            "programmes for SMEs in the Western Balkans. "
            "Sessions available online and on-campus; delivered in English and Bosnian."
        ),
        "link": "https://www.unmo.ba/en/lifelong-learning/digital-training/",
        "country": "BA",
        "offer_type": "training",
        "target_profile": "company",
        "org_token": "unmo",
        "domains": ["Digitalisation", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_project_unmo",
        "title": "UNMO – Western Balkans Innovation Network: Open Partnership Call",
        "summary": (
            "UNMO coordinates the Western Balkans Innovation Network and is seeking academic "
            "and industry partners to join applied research projects in digitalisation, "
            "sustainable development, and regional cohesion."
        ),
        "link": "https://www.unmo.ba/en/research/wbin/partner-call",
        "country": "BA",
        "offer_type": "project_opportunity",
        "target_profile": "researcher",
        "org_token": "unmo",
        "domains": ["Regional_development", "Innovation_and_entrepreneurship"],
    },

    # ── IPVC — Additional offers ───────────────────────────────────────────────
    {
        "token": "offer_training_researcher_ipvc",
        "title": "IPVC – Doctoral Training Event: Coastal & Marine Research Methods",
        "summary": (
            "IPVC organises an annual training workshop for doctoral researchers working on "
            "marine science, coastal engineering, and blue economy topics. "
            "Includes field excursions along the Minho estuary and Atlantic coastline."
        ),
        "link": "https://www.ipvc.pt/en/research/doctoral-training/coastal-methods/",
        "country": "PT",
        "offer_type": "training",
        "target_profile": "researcher",
        "org_token": "ipvc",
        "domains": ["Sustainability", "Regional_development"],
    },
    {
        "token": "offer_service_researcher_ipvc",
        "title": "IPVC – Marine Technology Expert Advisory Services",
        "summary": (
            "IPVC's marine engineering faculty provides expert consultancy on coastal monitoring, "
            "aquaculture system design, and ocean data analysis. "
            "Services are available to research teams and public institutions."
        ),
        "link": "https://www.ipvc.pt/en/research/expert-services/marine-technology/",
        "country": "PT",
        "offer_type": "service",
        "target_profile": "researcher",
        "org_token": "ipvc",
        "domains": ["Sustainability", "Technology_transfer"],
    },
    {
        "token": "offer_internship_ipvc",
        "title": "IPVC – Blue Economy Research Internship",
        "summary": (
            "IPVC offers a 3-month paid internship in its blue economy and marine sustainability "
            "research unit. Students assist with field data collection, GIS mapping, and report writing. "
            "Open to BSc and MSc students in environmental or marine sciences."
        ),
        "link": "https://www.ipvc.pt/en/research/internships/blue-economy/",
        "country": "PT",
        "offer_type": "internship",
        "target_profile": "student",
        "org_token": "ipvc",
        "domains": ["Sustainability", "Regional_development"],
    },
    {
        "token": "offer_training_company_ipvc",
        "title": "IPVC – Sustainable Tourism & Regional Development Training",
        "summary": (
            "IPVC provides short professional training programmes for tourism operators, "
            "local authorities, and SMEs on sustainable regional development, cultural heritage "
            "management, and eco-tourism best practices."
        ),
        "link": "https://www.ipvc.pt/en/continuing-education/sustainable-tourism/",
        "country": "PT",
        "offer_type": "training",
        "target_profile": "company",
        "org_token": "ipvc",
        "domains": ["Sustainability", "Regional_development"],
    },

    # ── EUC — Additional offers ────────────────────────────────────────────────
    {
        "token": "offer_research_group_euc",
        "title": "EUC – AI & Data Science Research Centre",
        "summary": (
            "The EUC AI and Data Science Research Centre conducts applied research in machine learning, "
            "natural language processing, and decision support systems. "
            "Open to collaboration with European research institutions and industry partners."
        ),
        "link": "https://www.euc.ac.cy/en/research/ai-data-science-centre/",
        "country": "CY",
        "offer_type": "research_group",
        "target_profile": "researcher",
        "org_token": "euc",
        "domains": ["AI", "Digitalisation"],
    },
    {
        "token": "offer_project_euc",
        "title": "EUC – Mediterranean Innovation Hub: Partner Search for EU Projects",
        "summary": (
            "EUC is forming consortia for Horizon Europe and COST Action calls focused on "
            "digital health, smart cities, and sustainable tourism in the Mediterranean region. "
            "Researchers from EU and associated countries are invited to express interest."
        ),
        "link": "https://www.euc.ac.cy/en/research/mediterranean-innovation-hub/",
        "country": "CY",
        "offer_type": "project_opportunity",
        "target_profile": "researcher",
        "org_token": "euc",
        "domains": ["AI", "Sustainability"],
    },
    {
        "token": "offer_thesis_euc",
        "title": "EUC – Thesis Positions: Smart City Technologies for Mediterranean Cities",
        "summary": (
            "EUC offers supervised thesis positions on smart city applications including "
            "intelligent transport systems, energy management, and civic digital services. "
            "Co-supervision with municipalities and private sector partners available."
        ),
        "link": "https://www.euc.ac.cy/en/research/thesis-opportunities/smart-city/",
        "country": "CY",
        "offer_type": "thesis",
        "target_profile": "student",
        "org_token": "euc",
        "domains": ["Digitalisation", "AI"],
    },
    {
        "token": "offer_funding_euc_company",
        "title": "EUC – TTO Industry Co-Funding Scheme for Cyprus-Based Companies",
        "summary": (
            "EUC's Technology Transfer Office connects local companies with research teams for "
            "co-funded R&D projects. Companies contribute 30% of costs; the remainder is covered "
            "by national R&D funds and EU instruments available to Cypriot entities."
        ),
        "link": "https://www.euc.ac.cy/en/research/tto/industry-cofunding/",
        "country": "CY",
        "offer_type": "funding_partner",
        "target_profile": "company",
        "org_token": "euc",
        "domains": ["Technology_transfer", "Innovation_and_entrepreneurship"],
    },

    # ── COMPANY — Lab ─────────────────────────────────────────────────────────
    {
        "token": "offer_lab_research_utc",
        "title": "UTC – Open Research Lab Access for Industry Partners",
        "summary": (
            "UTC grants industry partners access to its materials science, mechatronics, "
            "and chemical engineering labs under supervised usage agreements. "
            "Ideal for SMEs that lack in-house analytical equipment."
        ),
        "link": "https://www.utc.fr/en/research/labs/industry-access/",
        "country": "FR",
        "offer_type": "lab",
        "target_profile": "company",
        "org_token": "utc",
        "domains": ["Technology_transfer", "Innovation_and_entrepreneurship"],
    },
    {
        "token": "offer_lab_materials_univpm",
        "title": "UNIVPM – Advanced Materials & Testing Lab for Companies",
        "summary": (
            "UNIVPM's materials lab offers characterisation, fatigue testing, and additive "
            "manufacturing services to industrial clients. "
            "Capabilities include SEM, XRD, and 3D printing in metal and polymer."
        ),
        "link": "https://www.univpm.it/Entra/Engine/RAServePG.php/P/25251IT2601010/T/Materials-Lab-Industry",
        "country": "IT",
        "offer_type": "lab",
        "target_profile": "company",
        "org_token": "univpm",
        "domains": ["Technology_transfer", "Sustainability"],
    },
    {
        "token": "offer_lab_digital_euc",
        "title": "EUC – Digital Innovation Lab: Prototyping & Testing Space for Companies",
        "summary": (
            "European University Cyprus operates a digital innovation lab equipped with AR/VR stations, "
            "3D printers, electronics prototyping benches, and software development environments. "
            "Companies can book hourly or daily slots for product prototyping and user testing."
        ),
        "link": "https://www.euc.ac.cy/en/research/digital-innovation-lab/industry/",
        "country": "CY",
        "offer_type": "lab",
        "target_profile": "company",
        "org_token": "euc",
        "domains": ["Co_creation_and_testbeds", "Digitalisation"],
    },
]


class Command(BaseCommand):
    help = "Seeds sample published offers covering all filter types used in the frontend."

    @transaction.atomic
    def handle(self, *args, **options):
        bot = User.objects.get(username="ingestion_bot")
        source_type = SourceType.objects.get(name="manual")

        offer_type_map = {ot.name: ot for ot in OfferType.objects.all()}
        profile_map = {tp.name: tp for tp in TargetProfile.objects.all()}
        domain_map = {d.name: d for d in Domain.objects.all()}
        org_map = {str(o.id): o for o in Organization.objects.all()}

        org_token_map = {}
        for org in Organization.objects.all():
            from content.seeding import uuid_from_token as _u
            for token in ["unibz", "mdu", "tu_ilmenau", "uitm", "utc", "euc", "univpm", "unmo", "ipvc"]:
                if org.id == _u(token):
                    org_token_map[token] = org

        created = 0
        skipped = 0

        for spec in OFFERS:
            offer_type = offer_type_map.get(spec["offer_type"])
            target_profile = profile_map.get(spec["target_profile"])
            organization = org_token_map.get(spec["org_token"])

            if not offer_type:
                self.stdout.write(self.style.WARNING(f"  Unknown offer_type '{spec['offer_type']}' — skipping {spec['token']}"))
                skipped += 1
                continue
            if not target_profile:
                self.stdout.write(self.style.WARNING(f"  Unknown target_profile '{spec['target_profile']}' — skipping {spec['token']}"))
                skipped += 1
                continue
            if not organization:
                self.stdout.write(self.style.WARNING(f"  Unknown org_token '{spec['org_token']}' — skipping {spec['token']}"))
                skipped += 1
                continue

            offer, was_created = Offer.objects.update_or_create(
                id=uuid_from_token(spec["token"]),
                defaults={
                    "title": spec["title"],
                    "summary": spec["summary"],
                    "link": spec["link"],
                    "country": spec["country"],
                    "status": Offer.OfferStatus.PUBLISHED,
                    "offer_type": offer_type,
                    "target_profile": target_profile,
                    "organization": organization,
                    "source_type": source_type,
                    "created_by": bot,
                    "updated_by": bot,
                    "details": {"seeded": True},
                },
            )

            OfferDomain.objects.filter(offer=offer).delete()
            for domain_name in spec.get("domains", []):
                domain = domain_map.get(domain_name)
                if domain:
                    OfferDomain.objects.get_or_create(offer=offer, domain=domain)
                else:
                    self.stdout.write(self.style.WARNING(f"  Unknown domain '{domain_name}' for offer {spec['token']}"))

            action = "Created" if was_created else "Updated"
            self.stdout.write(f"  {action}: {spec['title'][:70]}")
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {created} offer(s) seeded, {skipped} skipped."
        ))
