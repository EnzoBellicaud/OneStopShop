export interface MockOpportunity {
  id: string;
  title: string;
  description: string;
  offer_type: string;
  target_profile: string;
  created_at: string;
}

export type MockOpportunityCreateRequest = {
  title: string;
  description: string;
  offer_type: string;
  target_profile: string;
};

export interface OfferTypeLookup {
  id: string;
  name: string;
  description: string;
}

export interface OfferTypeAdmin {
  id: string;
  name: string;
  description: string;
  keywords: string;
}
export interface OfferTypeAdminListResponse {
  count: number;
  results: OfferTypeAdmin[];
}
export type OfferTypeAdminCreateRequest = { name: string; description: string; keywords: string };
export type OfferTypeAdminPatchRequest = Partial<OfferTypeAdminCreateRequest>;

export interface DomainLookup {
  id: string;
  name: string;
}

export interface OrganizationLookup {
  id: string;
  name: string;
  type: string;
  country: string;
}

export interface TargetProfileLookup {
  id: string;
  name: string;
  description: string;
}

export interface CountryLookup {
  code: string;
}

export interface OrganizationSummary {
  id: string;
  name: string;
  type: string;
  country: string;
}

export interface OrganizationDetail {
  id: string;
  name: string;
  type: string;
  country: string;
  website: string;
  offers_count: number;
  sources_count: number;
}

export interface Offer {
  id: string;
  title: string;
  summary: string;
  link: string;
  country: string;
  status: string;
  offer_type: string;
  organization: OrganizationSummary;
  source_type: string;
  target_profile: string;
  domains: string[];
  details: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface OfferListResponse {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  limit: number;
  results: Offer[];
}

export interface ScrapingRunSummary {
  id: string;
  source_key: string;
  status: string;
  offers_processed: number;
  offers_created: number;
  offers_updated: number;
  offers_unchanged: number;
  offers_skipped: number;
  urls_neglected: number;
  errors_count: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ScrapingRunListResponse {
  count: number;
  results: ScrapingRunSummary[];
}

export interface ScrapingRunDetail extends ScrapingRunSummary {
  log: Array<Record<string, unknown>>;
  updated_at: string;
}

export interface LookupResponse<T> {
  count: number;
  results: T[];
}

export interface OfferQueryParams {
  q?: string;
  status?: string;
  offer_type?: string;
  organization?: string;
  target_profile?: string;
  domain?: string;
  country?: string;
  page?: number;
  page_size?: number;
  limit?: number;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface UserOrganization {
  id: string;
  name: string;
  role: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  bio: string;
  avatar_url: string | null;
  preferred_domains: string[];
  preferred_countries: string[];
  notification_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserSummary {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserDetail extends UserSummary {
  profile: UserProfile;
  organizations: UserOrganization[];
}

export interface UserUpdateRequest {
  email?: string;
  username?: string;
  profile?: Partial<UserProfile>;
}

export interface DashboardStats {
  active_needs_count: number;
  total_favorites: number;
  new_matches_count: number;
}

export interface NeedSummary {
  id: string;
  title: string;
}

export interface UserNeed {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'fulfilled' | 'archived';
  target_profile_id: string;
  domain_ids: string[];
  countries: string[];
  matching_hits_count: number;
  created_at: string;
  updated_at: string;
}

export interface UserNeedCreateRequest {
  title: string;
  description: string;
  target_profile_id: string;
  domain_ids: string[];
  countries: string[];
}

export interface UserNeedUpdateRequest extends UserNeedCreateRequest {
  status?: 'active' | 'fulfilled' | 'archived';
}

export interface OfferPreview {
  id: string;
  title: string;
  organization: string;
  link: string;
}

export interface UserFavorite {
  id: string;
  offer: OfferPreview;
  note: string | null;
  created_at: string;
}

export interface UserFavoriteCreateRequest {
  offer_id: string;
  note?: string | null;
}

export interface MatchingHit {
  id: string;
  need: NeedSummary;
  offer: OfferPreview;
  match_score: number;
  match_reason: string;
  status: 'new' | 'viewed' | 'interested' | 'declined';
  created_at: string;
  updated_at: string;
}

export interface MatchingHitUpdateRequest {
  status: 'viewed' | 'interested' | 'declined';
}

export interface DashboardResponse {
  user: UserDetail;
  stats: DashboardStats;
  recent_favorites: UserFavorite[];
  recent_matches: MatchingHit[];
}

export interface UserNeedsQueryParams {
  status?: 'active' | 'fulfilled' | 'archived';
  page?: number;
  page_size?: number;
}

export interface UserFavoritesQueryParams {
  page?: number;
  page_size?: number;
}

export interface MatchingHitsQueryParams {
  status?: 'new' | 'viewed' | 'interested' | 'declined';
  sort?: '-match_score' | 'created_at';
  page?: number;
  page_size?: number;
}

export interface AdminAccountStats {
  needs_count: number;
  favorites_count: number;
  offers_created: number;
  last_login: string | null;
}

export interface AdminUserDetail extends UserDetail {
  account_stats: AdminAccountStats;
}

export interface AdminUserUpdateRequest {
  username?: string;
  email?: string;
  is_active?: boolean;
}

export interface AdminUsersQueryParams {
  search?: string;
  page?: number;
  page_size?: number;
  created_after?: string;
  status?: 'active' | 'inactive';
}

export interface AdminUserNeed {
  id: string;
  title: string;
  status: 'active' | 'fulfilled' | 'archived';
  domains: string[];
  created_at: string;
  matching_hits_count: number;
}

export interface AdminUserFavorite {
  id: string;
  offer_id: string;
  offer: OfferPreview;
  note: string | null;
  created_at: string;
}

export interface AdminMatchingHit {
  id: string;
  need_id: string;
  need_title: string;
  offer_id: string;
  offer_title: string;
  match_score: number;
  status: 'new' | 'viewed' | 'interested' | 'declined';
  created_at: string;
}

export interface AnalyticsPeriod {
  from: string;
  to: string;
}

export interface AdminAnalyticsUserMetrics {
  total_users: number;
  active_users: number;
  new_users: number;
  deleted_users: number;
}

export interface AdminAnalyticsContentMetrics {
  total_needs: number;
  active_needs: number;
  fulfilled_needs: number;
  total_favorites: number;
  total_matches: number;
}

export interface AdminAnalyticsEngagementMetrics {
  avg_needs_per_user: number;
  avg_favorites_per_user: number;
  match_acceptance_rate: number;
  need_fulfillment_rate: number;
}

export interface AdminAnalyticsResponse {
  period: AnalyticsPeriod;
  user_metrics: AdminAnalyticsUserMetrics;
  content_metrics: AdminAnalyticsContentMetrics;
  engagement_metrics: AdminAnalyticsEngagementMetrics;
}

export interface OrganizationUserStats {
  count: number;
  active: number;
}

export interface AdminGrowthMetrics {
  last_7_days: number;
  last_30_days: number;
  trend: 'up' | 'down' | 'flat';
}

export interface AdminUserStatsResponse {
  total_users: number;
  active_users: number;
  inactive_users: number;
  by_status: Record<string, number>;
  by_organization: Record<string, OrganizationUserStats>;
  growth: AdminGrowthMetrics;
}

export interface AdminNeedsStats {
  total: number;
  active: number;
  fulfilled: number;
  archived: number;
  by_domain: Record<string, number>;
}

export interface AdminFavoritesStats {
  total: number;
  unique_offers: number;
  avg_per_user: number;
}

export interface AdminMatchingDistribution {
  excellent: number;
  good: number;
  fair: number;
}

export interface AdminMatchingStats {
  total_matches: number;
  avg_score: number;
  score_distribution: AdminMatchingDistribution;
}

export interface AdminContentStatsResponse {
  needs: AdminNeedsStats;
  favorites: AdminFavoritesStats;
  matching: AdminMatchingStats;
}

export interface TimelineBucket {
  bucket: string;
  runs: number;
  errors: number;
}

export interface ScrapingOverview {
  window: string;
  runs_total: number;
  runs_success: number;
  offers_processed: number;
  offers_created: number;
  offers_updated: number;
  urls_neglected_total: number;
  errors_total: number;
  runs_timeline: TimelineBucket[];
}

export interface SourceHealth {
  source_key: string;
  total_urls: number;
  pending: number;
  done: number;
  error: number;
  archived: number;
  last_scraped_at: string | null;
}

export interface SourcesHealthResponse {
  results: SourceHealth[];
}

export interface LlmStats {
  window: string;
  method_split: Record<string, number>;
  avg_confidence_llm: number | null;
  avg_confidence_deterministic: number | null;
}

export interface ImportValidRow {
  row: number;
  data: Record<string, string>;
  warnings: string[];
}

export interface ImportInvalidRow {
  row: number;
  data: Record<string, string>;
  errors: string[];
}

export interface PreviewResult {
  valid: ImportValidRow[];
  invalid: ImportInvalidRow[];
}

export interface ConfirmResult {
  drafts: number;
  published: number;
}

// ── User management ────────────────────────────────────────────────────────

export interface UserManagementSummary {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile: string;
  is_active: boolean;
  approval_status: 'pending' | 'approved' | 'rejected';
  email_verified: boolean;
  approved_by: string | null;
  approval_notes: string;
  organization_id: string | null;
  organization_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminUsersListQueryParams {
  search?: string;
  profile?: string;
  approval_status?: 'pending' | 'approved' | 'rejected';
  status?: 'active' | 'inactive';
  page?: number;
  page_size?: number;
}

export interface UserApprovalRequest {
  action?: 'approve' | 'reject';
  notes?: string;
  email_verified?: boolean;
}

export interface UserRoleRequest {
  profile: string;
}

export interface AdminCreateUserRequest {
  username: string;
  email: string;
  password: string;
  profile: string;
  first_name?: string;
  last_name?: string;
  organization_id?: string;
}

export interface AdminCreateOrgRequest {
  name: string;
  type: 'university' | 'company' | 'other';
  country: string;
  website?: string;
}

// ── Scraping sources ───────────────────────────────────────────────────────

export interface ScrapingSource {
  key: string;
  name: string;
  url: string;
  organization_id: string | null;
  organization_name: string | null;
  target_profile: 'student' | 'company' | 'researcher';
  country: string;
  domain_names: string[];
  interval_minutes: number;
  llm_fallback_enabled: boolean;
  enabled: boolean;
  quality: string;
  crawl_depth: number;
  crawl_max_pages: number;
  crawl_match_patterns: string[];
  crawl_exclude_patterns: string[];
  created_at: string;
  updated_at: string;
}

export interface ScrapingSourceListResponse {
  count: number;
  results: ScrapingSource[];
}

export type ScrapingSourceCreateRequest = Omit<ScrapingSource, 'created_at' | 'updated_at' | 'organization_name' | 'key' | 'quality'> & { organization_id: string };
export type ScrapingSourcePatchRequest = Partial<Omit<ScrapingSourceCreateRequest, 'key'>>;

// ── Allowed domains ────────────────────────────────────────────────────────

export interface AllowedDomainItem {
  id: string;
  domain: string;
  organization: string;
  organization_id: string;
  description: string;
  created_at: string;
}

export interface AllowedDomainCreateRequest {
  domain: string;
  organization_id: string;
  description?: string;
}

// ── Offer write ────────────────────────────────────────────────────────────

export interface OfferCreateRequest {
  title: string;
  summary: string;
  link: string;
  country: string;
  offer_type: string;
  target_profile: string;
  deadline?: string;
  status?: 'draft' | 'published' | 'archived';
  domains?: string[];
  organization_id?: string;
}

export type OfferUpdateRequest = Partial<OfferCreateRequest>;
