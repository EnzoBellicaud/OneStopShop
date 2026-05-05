from django.contrib import admin

from content.models import Offer, ScrapingJob, ScrapingRun


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
	list_display = ("title", "status", "offer_type", "organization", "updated_at")
	list_filter = ("status", "offer_type", "organization")
	search_fields = ("title", "link", "organization__name")


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
	list_display = (
		"key",
		"name",
		"source_domain",
		"is_active",
		"run_interval_minutes",
		"last_run_at",
	)
	list_filter = ("is_active", "status", "source_domain")
	search_fields = ("key", "name", "source_domain")


@admin.register(ScrapingRun)
class ScrapingRunAdmin(admin.ModelAdmin):
	list_display = (
		"source_key",
		"status",
		"offers_processed",
		"offers_created",
		"offers_updated",
		"offers_flagged_stale",
		"errors_count",
		"created_at",
	)
	list_filter = ("status", "source_key")
	search_fields = ("source_key",)
	readonly_fields = ("created_at", "updated_at", "started_at", "completed_at")
