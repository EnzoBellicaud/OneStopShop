def _openapi_spec() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "SUNRISE OSS API",
            "version": "1.0.0",
            "description": "API for offers, lookup tables, scraping run telemetry, and offer import operations.",
        },
        "servers": [{"url": "/"}],
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/lookups/offer-types": {
                "get": {
                    "summary": "List offer types",
                    "responses": {
                        "200": {
                            "description": "Offer type lookup entries",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/OfferTypeLookupResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/lookups/domains": {
                "get": {
                    "summary": "List domains",
                    "responses": {
                        "200": {
                            "description": "Domain lookup entries",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/DomainLookupResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/lookups/organizations": {
                "get": {
                    "summary": "List organizations",
                    "responses": {
                        "200": {
                            "description": "Organization lookup entries",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/OrganizationLookupResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/lookups/countries": {
                "get": {
                    "summary": "List countries used by offers",
                    "responses": {
                        "200": {
                            "description": "Country lookup entries",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CountryLookupResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/offers": {
                "get": {
                    "summary": "List offers",
                    "parameters": [
                        {"name": "q", "in": "query", "schema": {"type": "string"}},
                        {"name": "domain", "in": "query", "schema": {"type": "string"}},
                        {"name": "country", "in": "query", "schema": {"type": "string"}},
                        {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 200}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 200}},
                        {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["draft", "published", "archived"]}},
                        {"name": "offer_type", "in": "query", "schema": {"type": "string"}},
                        {"name": "organization", "in": "query", "schema": {"type": "string"}},
                        {"name": "target_profile", "in": "query", "schema": {"type": "string"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Offer list",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/OfferListResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/offers/{offer_id}": {
                "get": {
                    "summary": "Get offer by id",
                    "parameters": [
                        {"name": "offer_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Offer detail",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Offer"}}},
                        },
                        "400": {
                            "description": "Invalid offer id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "404": {
                            "description": "Offer not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/scraping/runs": {
                "get": {
                    "summary": "List scraping runs",
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 100}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Scraping run summaries",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ScrapingRunListResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/scraping/runs/{run_id}": {
                "get": {
                    "summary": "Get scraping run by id",
                    "parameters": [
                        {"name": "run_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Scraping run detail with full log",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ScrapingRunDetail"}
                                }
                            },
                        },
                        "400": {
                            "description": "Invalid run id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "404": {
                            "description": "Scraping run not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/scraping/overview": {
                "get": {
                    "summary": "Scraping activity overview",
                    "parameters": [
                        {"name": "window", "in": "query", "schema": {"type": "string", "enum": ["24h", "7d", "30d"]}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Aggregated scraping stats for time window",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ScrapingOverviewResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/scraping/sources/health": {
                "get": {
                    "summary": "Per-source crawl queue health from CrawlUrl table",
                    "responses": {
                        "200": {
                            "description": "URL queue stats per source key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SourcesHealthResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/scraping/llm/stats": {
                "get": {
                    "summary": "LLM extraction method and confidence stats",
                    "parameters": [
                        {"name": "window", "in": "query", "schema": {"type": "string", "enum": ["24h", "7d", "30d"]}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Method split and confidence averages",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LlmStatsResponse"}
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {"status": {"type": "string", "example": "ok"}},
                    "required": ["status"],
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "OfferTypeLookup": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["id", "name", "description"],
                },
                "OfferTypeLookupResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/OfferTypeLookup"}},
                    },
                    "required": ["count", "results"],
                },
                "DomainLookup": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                    },
                    "required": ["id", "name"],
                },
                "DomainLookupResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/DomainLookup"}},
                    },
                    "required": ["count", "results"],
                },
                "OrganizationLookup": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "country": {"type": "string"},
                    },
                    "required": ["id", "name", "type", "country"],
                },
                "OrganizationLookupResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/OrganizationLookup"}},
                    },
                    "required": ["count", "results"],
                },
                "CountryLookup": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                    },
                    "required": ["code"],
                },
                "CountryLookupResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/CountryLookup"}},
                    },
                    "required": ["count", "results"],
                },
                "OrganizationSummary": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "country": {"type": "string"},
                    },
                    "required": ["id", "name", "type", "country"],
                },
                "Offer": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "link": {"type": "string", "format": "uri"},
                        "country": {"type": "string"},
                        "status": {"type": "string", "enum": ["draft", "published", "archived"]},
                        "offer_type": {"type": "string"},
                        "organization": {"$ref": "#/components/schemas/OrganizationSummary"},
                        "source_type": {"type": "string"},
                        "target_profile": {"type": "string"},
                        "domains": {"type": "array", "items": {"type": "string"}},
                        "details": {"type": "object", "additionalProperties": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id", "title", "summary", "link", "country", "status", "offer_type", "organization",
                        "source_type", "target_profile", "domains", "details", "created_at", "updated_at"
                    ],
                },
                "OfferListResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "page": {"type": "integer"},
                        "page_size": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/Offer"}},
                    },
                    "required": ["count", "page", "page_size", "total_pages", "limit", "results"],
                },
                "ScrapingRunSummary": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "source_key": {"type": "string"},
                        "status": {"type": "string"},
                        "offers_processed": {"type": "integer"},
                        "offers_created": {"type": "integer"},
                        "offers_updated": {"type": "integer"},
                        "offers_unchanged": {"type": "integer"},
                        "urls_neglected": {"type": "integer"},
                        "errors_count": {"type": "integer"},
                        "started_at": {"type": "string", "format": "date-time", "nullable": True},
                        "completed_at": {"type": "string", "format": "date-time", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id", "source_key", "status", "offers_processed", "offers_created", "offers_updated",
                        "offers_unchanged", "urls_neglected", "errors_count", "started_at", "completed_at", "created_at"
                    ],
                },
                "ScrapingRunListResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/ScrapingRunSummary"}},
                    },
                    "required": ["count", "results"],
                },
                "ScrapingRunDetail": {
                    "allOf": [
                        {"$ref": "#/components/schemas/ScrapingRunSummary"},
                        {
                            "type": "object",
                            "properties": {
                                "log": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
                                "updated_at": {"type": "string", "format": "date-time"},
                            },
                            "required": ["log", "updated_at"],
                        },
                    ],
                },
                "ScrapingRunTimelineBucket": {
                    "type": "object",
                    "properties": {
                        "bucket": {"type": "string", "format": "date-time"},
                        "runs": {"type": "integer"},
                        "errors": {"type": "integer"},
                    },
                    "required": ["bucket", "runs", "errors"],
                },
                "ScrapingOverviewResponse": {
                    "type": "object",
                    "properties": {
                        "window": {"type": "string"},
                        "runs_total": {"type": "integer"},
                        "runs_success": {"type": "integer"},
                        "offers_processed": {"type": "integer"},
                        "offers_created": {"type": "integer"},
                        "offers_updated": {"type": "integer"},
                        "urls_neglected_total": {"type": "integer"},
                        "errors_total": {"type": "integer"},
                        "runs_timeline": {"type": "array", "items": {"$ref": "#/components/schemas/ScrapingRunTimelineBucket"}},
                    },
                    "required": [
                        "window", "runs_total", "runs_success",
                        "offers_processed", "offers_created", "offers_updated",
                        "urls_neglected_total", "errors_total", "runs_timeline"
                    ],
                },
                "SourceHealth": {
                    "type": "object",
                    "properties": {
                        "source_key": {"type": "string"},
                        "total_urls": {"type": "integer"},
                        "pending": {"type": "integer"},
                        "processing": {"type": "integer"},
                        "done": {"type": "integer"},
                        "error": {"type": "integer"},
                        "archived": {"type": "integer"},
                        "last_scraped_at": {"type": "string", "format": "date-time", "nullable": True},
                    },
                    "required": ["source_key", "total_urls", "pending", "processing", "done", "error", "archived", "last_scraped_at"],
                },
                "SourcesHealthResponse": {
                    "type": "object",
                    "properties": {
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/SourceHealth"}},
                    },
                    "required": ["results"],
                },
                "LlmStatsResponse": {
                    "type": "object",
                    "properties": {
                        "window": {"type": "string"},
                        "method_split": {"type": "object", "additionalProperties": {"type": "integer"}},
                        "avg_confidence_llm": {"type": "number", "nullable": True},
                        "avg_confidence_deterministic": {"type": "number", "nullable": True},
                    },
                    "required": ["window", "method_split", "avg_confidence_llm", "avg_confidence_deterministic"],
                },
            },
        },
    }
