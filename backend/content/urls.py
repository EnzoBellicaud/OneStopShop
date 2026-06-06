from django.urls import path

from content import views, auth
from content.views import admin_orgs as admin_orgs_views
from content.views import sources as sources_views
from content.views import admin_offer_types as offer_types_views

urlpatterns = [
    # Auth endpoints
    path("auth/register", auth.register, name="register"),
    path("auth/login", auth.login, name="login"),
    path("auth/refresh", auth.refresh_token, name="refresh-token"),
    path("auth/me", auth.get_current_user, name="get-current-user"),
    path("auth/me/update", auth.update_user_profile, name="update-user-profile"),
    path("auth/change-password", auth.change_password, name="change-password"),
    path("auth/logout", auth.logout, name="logout"),
    path("auth/verify-email", views.verify_email, name="verify-email"),

    # API documentation
    path("", views.api_docs, name="api-docs-home"),
    path("docs", views.api_docs, name="api-docs"),
    path("redoc", views.redoc_docs, name="api-redoc"),
    path("openapi.json", views.openapi_schema, name="openapi-schema"),
    path("health", views.health, name="health"),

    # Scraping endpoints
    path("scraping/runs", views.scraping_runs, name="scraping-runs"),
    path("scraping/runs/<str:run_id>", views.scraping_run_detail, name="scraping-run-detail"),
    path("scraping/overview", views.scraping_overview, name="scraping-overview"),
    path("scraping/sources/health", views.scraping_sources_health, name="scraping-sources-health"),
    path("scraping/llm/stats", views.scraping_llm_stats, name="scraping-llm-stats"),

    # Lookup endpoints
    path("lookups/offer-types", views.offer_types, name="offer-types"),
    path("lookups/domains", views.domains, name="domains"),
    path("lookups/organizations", views.organizations, name="organizations"),
    path("lookups/target-profiles", views.target_profiles, name="target-profiles"),
    path("lookups/countries", views.countries, name="countries"),

    # User management endpoints
    path("users", views.users_collection, name="users-collection"),
    path("users/<str:user_id>", views.user_resource, name="user-detail"),
    path("users/<str:user_id>/approval", views.user_approval, name="user-approval"),
    path("users/<str:user_id>/role", views.user_role, name="user-role"),
    path("users/<str:user_id>/organizations", views.link_user_organization, name="link-user-organization"),
    path("users/<str:user_id>/organizations/<str:org_id>", views.unlink_user_organization, name="unlink-user-organization"),
    path("users/<str:user_id>/dashboard", views.dashboard, name="user-dashboard"),
    path("users/<str:user_id>/needs", views.user_needs, name="user-needs"),
    path("users/<str:user_id>/needs/<str:need_id>", views.user_need_detail, name="user-need-detail"),
    path("users/<str:user_id>/favorites", views.user_favorites, name="user-favorites"),
    path("users/<str:user_id>/favorites/<str:offer_id>", views.user_favorite_detail, name="user-favorite-detail"),
    path("users/<str:user_id>/matching-hits", views.user_matching_hits, name="user-matching-hits"),
    path("users/<str:user_id>/matching-hits/<str:hit_id>", views.user_matching_hit_detail, name="user-matching-hit-detail"),
    # Admin endpoints
    path("admin/users", views.admin_user_collection, name="admin-user-collection"),
    path("admin/organizations", admin_orgs_views.admin_organization_collection, name="admin-organization-collection"),
    path("admin/sources", sources_views.admin_sources_collection, name="admin-sources"),
    path("admin/sources/<str:key>", sources_views.admin_source_detail, name="admin-source-detail"),
    path("admin/offer-types", offer_types_views.admin_offer_types_collection, name="admin-offer-types"),
    path("admin/offer-types/<str:offer_type_id>", offer_types_views.admin_offer_type_detail, name="admin-offer-type-detail"),
    path("admin/allowed-domains", views.allowed_domains_collection, name="allowed-domains"),
    path("admin/allowed-domains/<str:domain_id>", views.allowed_domain_resource, name="allowed-domain-resource"),

    # Offer endpoints
    path("offers/import/template", views.import_template, name="import-template"),
    path("offers/import/preview", views.import_preview, name="import-preview"),
    path("offers/import/confirm", views.import_confirm, name="import-confirm"),
    path("offers", views.offers, name="offers"),
    path("offers/<str:offer_id>", views.offer_detail, name="offer-detail"),

    # Forum endpoints
    path("forum/questions", views.forum_questions, name="forum-questions"),
    path("forum/questions/<str:question_id>", views.forum_question_detail, name="forum-question-detail"),
    path("forum/questions/<str:question_id>/answers", views.forum_answers, name="forum-answers"),
    path("forum/answers/<str:answer_id>", views.forum_answer_detail, name="forum-answer-detail"),
]
