import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  AdminCreateOrgRequest,
  AdminCreateUserRequest,
  AllowedDomainCreateRequest,
  AllowedDomainItem,
  AdminUsersListQueryParams,
  UserApprovalRequest,
  UserManagementSummary,
  DashboardResponse,
  ConfirmResult,
  CountryLookup,
  DomainLookup,
  ImportValidRow,
  LlmStats,
  LookupResponse,
  MatchingHit,
  MatchingHitsQueryParams,
  Offer,
  OfferCreateRequest,
  OfferListResponse,
  OfferQueryParams,
  OfferUpdateRequest,
  OrganizationLookup,
  OfferTypeLookup,
  PaginatedResponse,
  PreviewResult,
  ScrapingOverview,
  ScrapingRunDetail,
  ScrapingRunListResponse,
  TargetProfileLookup,
  UserDetail,
  UserFavorite,
  UserFavoriteCreateRequest,
  UserFavoritesQueryParams,
  UserNeed,
  UserNeedCreateRequest,
  UserNeedsQueryParams,
  UserNeedUpdateRequest,
  SourcesHealthResponse,
  ScrapingSource,
  ScrapingSourceListResponse,
  ScrapingSourceCreateRequest,
  ScrapingSourcePatchRequest,
} from './api.models';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class OssApiService {
  private readonly apiBaseUrl = environment.apiBaseUrl;

  constructor(private readonly http: HttpClient) {}

  getOfferTypes(): Observable<LookupResponse<OfferTypeLookup>> {
    return this.http.get<LookupResponse<OfferTypeLookup>>(`${this.apiBaseUrl}/lookups/offer-types`);
  }

  getDomains(): Observable<LookupResponse<DomainLookup>> {
    return this.http.get<LookupResponse<DomainLookup>>(`${this.apiBaseUrl}/lookups/domains`);
  }

  getOrganizations(): Observable<LookupResponse<OrganizationLookup>> {
    return this.http.get<LookupResponse<OrganizationLookup>>(`${this.apiBaseUrl}/lookups/organizations`);
  }

  getTargetProfiles(): Observable<LookupResponse<TargetProfileLookup>> {
    return this.http.get<LookupResponse<TargetProfileLookup>>(`${this.apiBaseUrl}/lookups/target-profiles`);
  }

  getCountries(): Observable<LookupResponse<CountryLookup>> {
    return this.http.get<LookupResponse<CountryLookup>>(`${this.apiBaseUrl}/lookups/countries`);
  }

  getOffers(query: OfferQueryParams): Observable<OfferListResponse> {
    return this.http.get<OfferListResponse>(`${this.apiBaseUrl}/offers`, {
      params: this.buildParams(query),
    });
  }

  updateOfferStatus(offerId: string, status: 'draft' | 'published' | 'archived'): Observable<Offer> {
    return this.http.patch<Offer>(`${this.apiBaseUrl}/offers/${offerId}`, { status });
  }

  getScrapingRuns(limit = 20): Observable<ScrapingRunListResponse> {
    return this.http.get<ScrapingRunListResponse>(`${this.apiBaseUrl}/scraping/runs`, {
      params: this.buildParams({ limit }),
    });
  }

  getScrapingRunDetail(runId: string): Observable<ScrapingRunDetail> {
    return this.http.get<ScrapingRunDetail>(`${this.apiBaseUrl}/scraping/runs/${runId}`);
  }

  getUser(userId: string): Observable<UserDetail> {
    return this.http.get<UserDetail>(`${this.apiBaseUrl}/users/${userId}`);
  }

  getDashboard(userId: string): Observable<DashboardResponse> {
    return this.http.get<DashboardResponse>(`${this.apiBaseUrl}/users/${userId}/dashboard`);
  }

  getNeeds(userId: string, query: UserNeedsQueryParams): Observable<LookupResponse<UserNeed> & { next: string | null; previous: string | null }> {
    return this.http.get<LookupResponse<UserNeed> & { next: string | null; previous: string | null }>(
      `${this.apiBaseUrl}/users/${userId}/needs`,
      { params: this.buildParams(query) },
    );
  }

  createNeed(userId: string, payload: UserNeedCreateRequest): Observable<UserNeed> {
    return this.http.post<UserNeed>(`${this.apiBaseUrl}/users/${userId}/needs`, payload);
  }

  updateNeed(userId: string, needId: string, payload: UserNeedUpdateRequest): Observable<UserNeed> {
    return this.http.put<UserNeed>(`${this.apiBaseUrl}/users/${userId}/needs/${needId}`, payload);
  }

  deleteNeed(userId: string, needId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/users/${userId}/needs/${needId}`);
  }

  getFavorites(
    userId: string,
    query: UserFavoritesQueryParams,
  ): Observable<LookupResponse<UserFavorite> & { next: string | null; previous: string | null }> {
    return this.http.get<LookupResponse<UserFavorite> & { next: string | null; previous: string | null }>(
      `${this.apiBaseUrl}/users/${userId}/favorites`,
      { params: this.buildParams(query) },
    );
  }

  addFavorite(userId: string, payload: UserFavoriteCreateRequest): Observable<UserFavorite> {
    return this.http.post<UserFavorite>(`${this.apiBaseUrl}/users/${userId}/favorites`, payload);
  }

  removeFavorite(userId: string, offerId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/users/${userId}/favorites/${offerId}`);
  }

  getMatchingHits(
    userId: string,
    query: MatchingHitsQueryParams,
  ): Observable<LookupResponse<MatchingHit> & { next: string | null; previous: string | null }> {
    return this.http.get<LookupResponse<MatchingHit> & { next: string | null; previous: string | null }>(
      `${this.apiBaseUrl}/users/${userId}/matching-hits`,
      { params: this.buildParams(query) },
    );
  }

  updateMatchingHit(userId: string, hitId: string, status: 'viewed' | 'interested' | 'declined'): Observable<MatchingHit> {
    return this.http.patch<MatchingHit>(`${this.apiBaseUrl}/users/${userId}/matching-hits/${hitId}`, { status });
  }

  getScrapingOverview(window: '24h' | '7d' | '30d' = '24h'): Observable<ScrapingOverview> {
    return this.http.get<ScrapingOverview>(`${this.apiBaseUrl}/scraping/overview`, {
      params: this.buildParams({ window }),
    });
  }

  getSourcesHealth(): Observable<SourcesHealthResponse> {
    return this.http.get<SourcesHealthResponse>(`${this.apiBaseUrl}/scraping/sources/health`);
  }

  getLlmStats(window: '24h' | '7d' | '30d' = '24h'): Observable<LlmStats> {
    return this.http.get<LlmStats>(`${this.apiBaseUrl}/scraping/llm/stats`, {
      params: this.buildParams({ window }),
    });
  }

  previewImport(file: File): Observable<PreviewResult> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<PreviewResult>(`${this.apiBaseUrl}/offers/import/preview`, form);
  }

  confirmImport(rows: (ImportValidRow & { status: 'draft' | 'published' })[]): Observable<ConfirmResult> {
    return this.http.post<ConfirmResult>(`${this.apiBaseUrl}/offers/import/confirm`, { rows });
  }

  // ── User management ──────────────────────────────────────────────────────

  getUsers(params?: Partial<AdminUsersListQueryParams>): Observable<PaginatedResponse<UserManagementSummary>> {
    return this.http.get<PaginatedResponse<UserManagementSummary>>(`${this.apiBaseUrl}/users`, {
      params: this.buildParams(params ?? {}),
    });
  }

  approveUser(userId: string, payload: UserApprovalRequest): Observable<UserManagementSummary> {
    return this.http.patch<UserManagementSummary>(`${this.apiBaseUrl}/users/${userId}/approval`, payload);
  }

  changeUserRole(userId: string, profile: string): Observable<UserManagementSummary> {
    return this.http.patch<UserManagementSummary>(`${this.apiBaseUrl}/users/${userId}/role`, { profile });
  }

  updateUser(userId: string, payload: { is_active?: boolean }): Observable<UserManagementSummary> {
    return this.http.patch<UserManagementSummary>(`${this.apiBaseUrl}/users/${userId}`, payload);
  }

  createAdminUser(payload: AdminCreateUserRequest): Observable<UserManagementSummary> {
    return this.http.post<UserManagementSummary>(`${this.apiBaseUrl}/admin/users`, payload);
  }

  linkUserOrganization(userId: string, organizationId: string): Observable<{ id: string; name: string; role: string }> {
    return this.http.post<{ id: string; name: string; role: string }>(
      `${this.apiBaseUrl}/users/${userId}/organizations`,
      { organization_id: organizationId }
    );
  }

  createOrganization(payload: AdminCreateOrgRequest): Observable<OrganizationLookup> {
    return this.http.post<OrganizationLookup>(`${this.apiBaseUrl}/admin/organizations`, payload);
  }

  // ── Allowed domains ───────────────────────────────────────────────────────

  getAllowedDomains(): Observable<LookupResponse<AllowedDomainItem>> {
    return this.http.get<LookupResponse<AllowedDomainItem>>(`${this.apiBaseUrl}/admin/allowed-domains`);
  }

  createAllowedDomain(payload: AllowedDomainCreateRequest): Observable<AllowedDomainItem> {
    return this.http.post<AllowedDomainItem>(`${this.apiBaseUrl}/admin/allowed-domains`, payload);
  }

  updateAllowedDomain(id: string, payload: Partial<AllowedDomainCreateRequest>): Observable<AllowedDomainItem> {
    return this.http.patch<AllowedDomainItem>(`${this.apiBaseUrl}/admin/allowed-domains/${id}`, payload);
  }

  deleteAllowedDomain(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/admin/allowed-domains/${id}`);
  }

  // ── Offer write ───────────────────────────────────────────────────────────

  createOffer(payload: OfferCreateRequest): Observable<Offer> {
    return this.http.post<Offer>(`${this.apiBaseUrl}/offers`, payload);
  }

  updateOffer(offerId: string, payload: OfferUpdateRequest): Observable<Offer> {
    return this.http.patch<Offer>(`${this.apiBaseUrl}/offers/${offerId}`, payload);
  }

  deleteOffer(offerId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/offers/${offerId}`);
  }

  getImportTemplate(): void {
    this.http.get(`${this.apiBaseUrl}/offers/import/template`, { responseType: 'blob' }).subscribe(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'oss_import_template.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // ── Scraping sources ─────────────────────────────────────────────────────

  getScrapingSources(): Observable<ScrapingSourceListResponse> {
    return this.http.get<ScrapingSourceListResponse>(`${this.apiBaseUrl}/admin/sources`);
  }

  createScrapingSource(payload: ScrapingSourceCreateRequest): Observable<ScrapingSource> {
    return this.http.post<ScrapingSource>(`${this.apiBaseUrl}/admin/sources`, payload);
  }

  patchScrapingSource(key: string, payload: ScrapingSourcePatchRequest): Observable<ScrapingSource> {
    return this.http.patch<ScrapingSource>(`${this.apiBaseUrl}/admin/sources/${key}`, payload);
  }

  deleteScrapingSource(key: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/admin/sources/${key}`);
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  changePassword(oldPassword: string, newPassword: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${this.apiBaseUrl}/auth/change-password`, {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  private buildParams(
    query: OfferQueryParams | Record<string, string | number | undefined>,
  ): HttpParams {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === '') {
        continue;
      }
      params = params.set(key, String(value));
    }
    return params;
  }
}
