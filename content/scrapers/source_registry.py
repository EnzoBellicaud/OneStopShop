from content.scrapers.types import SourceDefinition


SOURCE_REGISTRY: list[SourceDefinition] = [
    SourceDefinition(
        key="unibz_master_software_engineering",
        name="UNIBZ Master in Software Engineering",
        url="https://www.unibz.it/en/faculties/engineering/master-software-engineering/",
        organization_token="unibz",
        offer_type="training",
        target_profile="student",
        country="IT",
        domain_names=["AI", "Digitalisation", "Industry_collaboration"],
    ),
    SourceDefinition(
        key="unibz_phd_computer_science",
        name="UNIBZ PhD in Computer Science",
        url="https://www.unibz.it/en/faculties/engineering/phd-computer-science/",
        organization_token="unibz",
        offer_type="training",
        target_profile="researcher",
        country="IT",
        domain_names=["AI", "Digitalisation"],
    ),
    SourceDefinition(
        key="unibz_bachelor_computer_science",
        name="UNIBZ Bachelor in Computer Science",
        url="https://www.unibz.it/en/faculties/engineering/bachelor-computer-science/",
        organization_token="unibz",
        offer_type="training",
        target_profile="student",
        country="IT",
        domain_names=["Digitalisation", "Cybersecurity"],
    ),
    SourceDefinition(
        key="unibz_erasmus_mobility",
        name="UNIBZ International Mobility",
        url="https://www.unibz.it/en/applicants/international/",
        organization_token="unibz",
        offer_type="mobility",
        target_profile="student",
        country="IT",
        domain_names=["Mobility"],
    ),
    SourceDefinition(
        key="mdu_fas_licentiate_thesis",
        name="MDU Research Schools Thesis Track",
        url="https://www.mdu.se/en/malardalen-university/research/research-schools",
        organization_token="mdu",
        offer_type="thesis",
        target_profile="researcher",
        country="SE",
        domain_names=["Robotics", "AI"],
    ),
    SourceDefinition(
        key="mdu_embedded_systems_research_group",
        name="MDU Embedded Systems Research Group",
        url="https://www.mdu.se/en/malardalen-university/research/research-specialisations/embedded-systems",
        organization_token="mdu",
        offer_type="research_group",
        target_profile="researcher",
        country="SE",
        domain_names=["Robotics", "AI"],
    ),
    SourceDefinition(
        key="mdu_din_funding_partner",
        name="MDU DIN Funding Partner",
        url="https://www.mdu.se/en/malardalen-university/research/research-specialisations/innovation-and-product-realisation",
        organization_token="mdu",
        offer_type="funding_partner",
        target_profile="company",
        country="SE",
        domain_names=["Industry_collaboration", "Innovation_and_entrepreneurship"],
    ),
]


def get_sources(source_keys: list[str] | None = None) -> list[SourceDefinition]:
    if not source_keys:
        return [source for source in SOURCE_REGISTRY if source.enabled]

    source_key_set = set(source_keys)
    return [
        source
        for source in SOURCE_REGISTRY
        if source.enabled and source.key in source_key_set
    ]
