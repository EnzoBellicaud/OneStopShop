def _openapi_spec() -> dict:
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "SUNRISE OSS API",
            "version": "1.0.0",
            "description": "API for offers, lookup tables, scraping run telemetry, and offer import operations.",
        },
        "servers": [{"url": "/"}],
        "tags": [
            {"name": "System", "description": "Health and API status endpoints."},
            {"name": "Lookups", "description": "Reference data used by forms and filters."},
            {"name": "Offers", "description": "Offer listing, detail, manual creation, update, and deletion."},
            {"name": "Users", "description": "User profile, dashboard, and organization operations."},
            {"name": "Needs", "description": "User need management."},
            {"name": "Favorites", "description": "User saved offers."},
            {"name": "Matching", "description": "Matching hit operations."},
            {"name": "Scraping", "description": "Scraping runs, telemetry, source health, and LLM stats."},
        ],
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
                },
                "post": {
                    "summary": "Create manual offer",
                    "description": "Admin, teacher, or company users only. Teachers and companies create offers for their linked organization.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OfferCreateRequest"}}},
                    },
                    "responses": {
                        "201": {
                            "description": "Offer created",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Offer"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "401": {
                            "description": "Authentication required",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "403": {
                            "description": "Insufficient permissions or no linked organization",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "404": {
                            "description": "Organization, offer type, or target profile not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                    },
                },
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
                },
                "patch": {
                    "summary": "Update manual offer",
                    "description": "Admin, teacher, or company users only. Teachers and companies can only update offers from their linked organization.",
                    "parameters": [
                        {"name": "offer_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OfferUpdateRequest"}}},
                    },
                    "responses": {
                        "200": {
                            "description": "Offer updated",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Offer"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "401": {
                            "description": "Authentication required",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "403": {
                            "description": "Insufficient permissions",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "404": {
                            "description": "Offer, offer type, or target profile not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                    },
                },
                "delete": {
                    "summary": "Delete manual offer",
                    "description": "Admin, teacher, or company users only. Teachers and companies can only delete offers from their linked organization.",
                    "parameters": [
                        {"name": "offer_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                    ],
                    "responses": {
                        "204": {"description": "Offer deleted"},
                        "401": {
                            "description": "Authentication required",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "403": {
                            "description": "Insufficient permissions",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                        "404": {
                            "description": "Offer not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                        },
                    },
                },
            },
            "/api/users": {
                "get": {
                    "summary": "List dashboard users",
                    "description": "Admin only.",
                    "parameters": [
                        {"name": "search", "in": "query", "schema": {"type": "string"}},
                        {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["active", "inactive"]}},
                        {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 200}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated users",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserListResponse"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "401": {
                            "description": "Authentication required",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "403": {
                            "description": "Admin access required",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/users/{user_id}": {
                "get": {
                    "summary": "Get dashboard user",
                    "description": "Admin only.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "responses": {
                        "200": {
                            "description": "User detail",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserDetail"}}},
                        },
                        "400": {
                            "description": "Invalid user id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
                "patch": {
                    "summary": "Update dashboard user",
                    "description": "Admin only.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserUpdateRequest"}}},
                    },
                    "responses": {
                        "200": {
                            "description": "Updated user detail",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserDetail"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "409": {
                            "description": "User conflict",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
                "delete": {
                    "summary": "Soft-delete dashboard user",
                    "description": "Admin only.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "responses": {
                        "204": {"description": "User soft-deleted"},
                        "400": {
                            "description": "Invalid user id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
            },
            "/api/users/{user_id}/organizations": {
                "post": {
                    "summary": "Link user to organization",
                    "description": "Authenticated user can link themself as member. Admins can assign allowed roles.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserOrganizationLinkRequest"}}},
                    },
                    "responses": {
                        "201": {
                            "description": "Organization link created",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserOrganization"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User or organization not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "409": {
                            "description": "Organization already linked",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/users/{user_id}/organizations/{org_id}": {
                "delete": {
                    "summary": "Unlink user organization",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "org_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    ],
                    "responses": {
                        "204": {"description": "Organization link removed"},
                        "400": {
                            "description": "Invalid id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User or organization link not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/users/{user_id}/dashboard": {
                "get": {
                    "summary": "Get user dashboard",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "responses": {
                        "200": {
                            "description": "Dashboard summary",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DashboardResponse"}}},
                        },
                        "400": {
                            "description": "Invalid user id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/users/{user_id}/needs": {
                "get": {
                    "summary": "List user needs",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "status", "in": "query", "schema": {"$ref": "#/components/schemas/UserNeedStatus"}},
                        {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 200}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated needs",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserNeedListResponse"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
                "post": {
                    "summary": "Create user need",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserNeedCreateRequest"}}},
                    },
                    "responses": {
                        "201": {
                            "description": "Need created",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserNeed"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User, target profile, or domain not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
            },
            "/api/users/{user_id}/needs/{need_id}": {
                "put": {
                    "summary": "Update user need",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "need_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserNeedUpdateRequest"}}},
                    },
                    "responses": {
                        "200": {
                            "description": "Need updated",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserNeed"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User, need, target profile, or domain not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
                "delete": {
                    "summary": "Delete user need",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "need_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    ],
                    "responses": {
                        "204": {"description": "Need deleted"},
                        "400": {
                            "description": "Invalid id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User or need not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
            },
            "/api/users/{user_id}/favorites": {
                "get": {
                    "summary": "List user favorites",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 200}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated favorites",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserFavoriteListResponse"}}},
                        },
                        "400": {
                            "description": "Invalid user id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
                "post": {
                    "summary": "Add user favorite",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [{"$ref": "#/components/parameters/UserId"}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserFavoriteCreateRequest"}}},
                    },
                    "responses": {
                        "201": {
                            "description": "Favorite added",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserFavorite"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User or offer not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "409": {
                            "description": "Offer already favorited",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                },
            },
            "/api/users/{user_id}/favorites/{offer_id}": {
                "delete": {
                    "summary": "Remove user favorite",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "offer_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    ],
                    "responses": {
                        "204": {"description": "Favorite removed"},
                        "400": {
                            "description": "Invalid id",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User or favorite not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/users/{user_id}/matching-hits": {
                "get": {
                    "summary": "List user matching hits",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "status", "in": "query", "schema": {"$ref": "#/components/schemas/MatchingHitStatus"}},
                        {"name": "sort", "in": "query", "schema": {"type": "string", "enum": ["-match_score", "created_at"]}},
                        {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 200}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated matching hits",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MatchingHitListResponse"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                    },
                }
            },
            "/api/users/{user_id}/matching-hits/{hit_id}": {
                "patch": {
                    "summary": "Update matching hit status",
                    "description": "Admin or the authenticated user themself.",
                    "parameters": [
                        {"$ref": "#/components/parameters/UserId"},
                        {"name": "hit_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MatchingHitUpdateRequest"}}},
                    },
                    "responses": {
                        "200": {
                            "description": "Matching hit updated",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MatchingHit"}}},
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
                        },
                        "404": {
                            "description": "User or matching hit not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserApiErrorResponse"}}},
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
            "parameters": {
                "UserId": {
                    "name": "user_id",
                    "in": "path",
                    "required": True,
                    "description": "User UUID. Authenticated self-service endpoints also accept `me`.",
                    "schema": {"type": "string"},
                },
            },
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
                "OfferContact": {
                    "type": "object",
                    "nullable": True,
                    "properties": {
                        "contact_id": {"type": "string", "format": "uuid"},
                        "role_label": {"type": "string", "example": "primary_contact"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email", "nullable": True},
                        "phone": {"type": "string", "nullable": True},
                        "linkedin": {"type": "string", "format": "uri", "nullable": True},
                    },
                    "required": ["contact_id", "role_label", "name", "email", "phone", "linkedin"],
                },
                "OfferContactInput": {
                    "type": "object",
                    "nullable": True,
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email", "nullable": True},
                        "phone": {"type": "string", "nullable": True},
                        "linkedin": {"type": "string", "format": "uri", "nullable": True},
                        "role": {"type": "string", "nullable": True},
                        "role_id": {"type": "string", "format": "uuid", "nullable": True},
                    },
                    "required": ["name"],
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
                        "deadline": {"type": "string", "format": "date", "nullable": True},
                        "contact": {"$ref": "#/components/schemas/OfferContact"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id", "title", "summary", "link", "country", "status", "offer_type", "organization",
                        "source_type", "target_profile", "domains", "details", "deadline", "contact",
                        "created_at", "updated_at"
                    ],
                },
                "OfferCreateRequest": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "link": {"type": "string", "format": "uri"},
                        "country": {"type": "string", "minLength": 2, "maxLength": 2},
                        "offer_type": {"type": "string"},
                        "target_profile": {"type": "string"},
                        "organization_id": {
                            "type": "string",
                            "format": "uuid",
                            "description": "Required for admin users. Ignored for teacher/company users.",
                        },
                        "status": {"type": "string", "enum": ["draft", "published", "archived"], "default": "draft"},
                        "deadline": {"type": "string", "format": "date", "nullable": True},
                        "domains": {"type": "array", "items": {"type": "string"}},
                        "contact": {"$ref": "#/components/schemas/OfferContactInput"},
                    },
                    "required": ["title", "summary", "link", "country", "offer_type", "target_profile"],
                },
                "OfferUpdateRequest": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "link": {"type": "string", "format": "uri"},
                        "country": {"type": "string", "minLength": 2, "maxLength": 2},
                        "status": {"type": "string", "enum": ["draft", "published", "archived"]},
                        "deadline": {"type": "string", "format": "date", "nullable": True},
                        "offer_type": {"type": "string"},
                        "target_profile": {"type": "string"},
                        "domains": {"type": "array", "items": {"type": "string"}},
                        "contact": {"$ref": "#/components/schemas/OfferContactInput"},
                    },
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
                "UserApiErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["error", "message"],
                },
                "UserProfile": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "user_id": {"type": "string", "format": "uuid"},
                        "bio": {"type": "string"},
                        "avatar_url": {"type": "string", "nullable": True},
                        "preferred_domains": {"type": "array", "items": {"type": "string"}},
                        "preferred_countries": {"type": "array", "items": {"type": "string"}},
                        "notification_enabled": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id", "user_id", "bio", "avatar_url", "preferred_domains", "preferred_countries",
                        "notification_enabled", "created_at", "updated_at"
                    ],
                },
                "UserOrganization": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                    },
                    "required": ["id", "name", "role"],
                },
                "UserDetail": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "is_active": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                        "profile": {"$ref": "#/components/schemas/UserProfile"},
                        "organizations": {"type": "array", "items": {"$ref": "#/components/schemas/UserOrganization"}},
                    },
                    "required": [
                        "id", "username", "email", "is_active", "created_at", "updated_at",
                        "profile", "organizations"
                    ],
                },
                "UserProfileRequest": {
                    "type": "object",
                    "properties": {
                        "bio": {"type": "string"},
                        "avatar_url": {"type": "string", "nullable": True},
                        "preferred_domains": {"type": "array", "items": {"type": "string"}},
                        "preferred_countries": {"type": "array", "items": {"type": "string"}},
                        "notification_enabled": {"type": "boolean"},
                    },
                },
                "UserUpdateRequest": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "username": {"type": "string"},
                        "profile": {"$ref": "#/components/schemas/UserProfileRequest"},
                    },
                },
                "UserListResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/UserDetail"}},
                    },
                    "required": ["count", "next", "previous", "results"],
                },
                "UserOrganizationLinkRequest": {
                    "type": "object",
                    "properties": {
                        "organization_id": {"type": "string", "format": "uuid"},
                        "role": {"type": "string", "default": "member"},
                    },
                    "required": ["organization_id"],
                },
                "DashboardStats": {
                    "type": "object",
                    "properties": {
                        "active_needs_count": {"type": "integer"},
                        "total_favorites": {"type": "integer"},
                        "new_matches_count": {"type": "integer"},
                    },
                    "required": ["active_needs_count", "total_favorites", "new_matches_count"],
                },
                "UserNeedStatus": {
                    "type": "string",
                    "enum": ["active", "fulfilled", "archived"],
                },
                "UserNeed": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {"$ref": "#/components/schemas/UserNeedStatus"},
                        "target_profile_id": {"type": "string", "format": "uuid"},
                        "domain_ids": {"type": "array", "items": {"type": "string", "format": "uuid"}},
                        "countries": {"type": "array", "items": {"type": "string"}},
                        "matching_hits_count": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id", "title", "description", "status", "target_profile_id", "domain_ids",
                        "countries", "matching_hits_count", "created_at", "updated_at"
                    ],
                },
                "UserNeedCreateRequest": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "target_profile_id": {"type": "string", "format": "uuid"},
                        "domain_ids": {"type": "array", "items": {"type": "string", "format": "uuid"}},
                        "countries": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "description", "target_profile_id", "domain_ids", "countries"],
                },
                "UserNeedUpdateRequest": {
                    "allOf": [
                        {"$ref": "#/components/schemas/UserNeedCreateRequest"},
                        {
                            "type": "object",
                            "properties": {"status": {"$ref": "#/components/schemas/UserNeedStatus"}},
                        },
                    ],
                },
                "OfferPreview": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "title": {"type": "string"},
                        "organization": {"type": "string"},
                        "link": {"type": "string", "format": "uri"},
                    },
                    "required": ["id", "title", "organization", "link"],
                },
                "UserFavorite": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "offer": {"$ref": "#/components/schemas/OfferPreview"},
                        "note": {"type": "string", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                    },
                    "required": ["id", "offer", "note", "created_at"],
                },
                "UserFavoriteCreateRequest": {
                    "type": "object",
                    "properties": {
                        "offer_id": {"type": "string", "format": "uuid"},
                        "note": {"type": "string", "nullable": True},
                    },
                    "required": ["offer_id"],
                },
                "NeedSummary": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "title": {"type": "string"},
                    },
                    "required": ["id", "title"],
                },
                "MatchingHitStatus": {
                    "type": "string",
                    "enum": ["new", "viewed", "interested", "declined"],
                },
                "MatchingHit": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "need": {"$ref": "#/components/schemas/NeedSummary"},
                        "offer": {"$ref": "#/components/schemas/OfferPreview"},
                        "match_score": {"type": "number"},
                        "match_reason": {"type": "string"},
                        "status": {"$ref": "#/components/schemas/MatchingHitStatus"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id", "need", "offer", "match_score", "match_reason",
                        "status", "created_at", "updated_at"
                    ],
                },
                "MatchingHitUpdateRequest": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["viewed", "interested", "declined"]},
                    },
                    "required": ["status"],
                },
                "DashboardResponse": {
                    "type": "object",
                    "properties": {
                        "user": {"$ref": "#/components/schemas/UserDetail"},
                        "stats": {"$ref": "#/components/schemas/DashboardStats"},
                        "recent_favorites": {"type": "array", "items": {"$ref": "#/components/schemas/UserFavorite"}},
                        "recent_matches": {"type": "array", "items": {"$ref": "#/components/schemas/MatchingHit"}},
                    },
                    "required": ["user", "stats", "recent_favorites", "recent_matches"],
                },
                "UserNeedListResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/UserNeed"}},
                    },
                    "required": ["count", "next", "previous", "results"],
                },
                "UserFavoriteListResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/UserFavorite"}},
                    },
                    "required": ["count", "next", "previous", "results"],
                },
                "MatchingHitListResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {"type": "array", "items": {"$ref": "#/components/schemas/MatchingHit"}},
                    },
                    "required": ["count", "next", "previous", "results"],
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
    _apply_openapi_tags(spec)
    return spec


def _apply_openapi_tags(spec: dict) -> None:
    for path, path_item in spec.get("paths", {}).items():
        tag = _tag_for_path(path)
        for operation_name, operation in path_item.items():
            if operation_name in {"get", "post", "put", "patch", "delete"}:
                operation.setdefault("tags", [tag])


def _tag_for_path(path: str) -> str:
    if path.startswith("/api/lookups/"):
        return "Lookups"
    if path.startswith("/api/offers"):
        return "Offers"
    if "/needs" in path:
        return "Needs"
    if "/favorites" in path:
        return "Favorites"
    if "/matching-hits" in path:
        return "Matching"
    if path.startswith("/api/users"):
        return "Users"
    if path.startswith("/api/scraping/"):
        return "Scraping"
    return "System"
