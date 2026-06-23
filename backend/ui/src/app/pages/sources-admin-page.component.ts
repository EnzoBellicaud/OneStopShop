import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import {
  OrganizationLookup,
  ScrapingSource,
  ScrapingSourceCreateRequest,
} from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';
import { AuthService } from '../shared/auth.service';

@Component({
  selector: 'app-sources-admin-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sources-admin-page.component.html',
  styleUrl: './sources-admin-page.component.css',
})
export class SourcesAdminPageComponent implements OnInit, OnDestroy {
  sources: ScrapingSource[] = [];
  organizations: OrganizationLookup[] = [];
  loading = false;
  sourceModalTarget: ScrapingSource | null = null;
  criteriaModalSource: ScrapingSource | null = null;
  showSourceModal = false;
  savingSource = signal(false);
  deletingSource = signal<string | null>(null);
  sourceForm: ScrapingSourceCreateRequest = this.emptySourceForm();
  errorMessage = '';

  private readonly destroy$ = new Subject<void>();

  constructor(private readonly api: OssApiService, public readonly auth: AuthService) {}

  ngOnInit(): void {
    this.loadSources();
    if (!this.auth.isTeacher) {
      this.api.getOrganizations()
        .pipe(takeUntil(this.destroy$))
        .subscribe({ next: (res) => { this.organizations = res.results; } });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadSources(): void {
    this.loading = true;
    this.api.getScrapingSources().pipe(takeUntil(this.destroy$)).subscribe({
      next: (res) => { this.sources = res.results; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  openCreateSource(): void {
    this.sourceModalTarget = null;
    this.sourceForm = this.emptySourceForm();
    this.errorMessage = '';
    this.showSourceModal = true;
  }

  openEditSource(src: ScrapingSource): void {
    this.sourceModalTarget = src;
    this.sourceForm = {
      name: src.name,
      url: src.url,
      organization_id: src.organization_id ?? '',
      target_profile: src.target_profile,
      country: src.country,
      domain_names: [...src.domain_names],
      interval_minutes: src.interval_minutes,
      llm_fallback_enabled: src.llm_fallback_enabled,
      enabled: src.enabled,
      crawl_depth: src.crawl_depth,
      crawl_max_pages: src.crawl_max_pages,
      crawl_match_patterns: [...src.crawl_match_patterns],
      crawl_exclude_patterns: [...src.crawl_exclude_patterns],
      auto_publish_enabled: src.auto_publish_enabled,
      auto_publish_mode: src.auto_publish_mode,
    };
    this.errorMessage = '';
    this.showSourceModal = true;
  }

  closeSourceModal(): void {
    this.showSourceModal = false;
    this.errorMessage = '';
  }

  openCriteriaModal(src: ScrapingSource): void {
    this.criteriaModalSource = src;
  }

  closeCriteriaModal(): void {
    this.criteriaModalSource = null;
  }

  criteriaMode(source: Pick<ScrapingSource, 'llm_fallback_enabled'> | ScrapingSourceCreateRequest): 'LLM' | 'Deterministic' {
    return source.llm_fallback_enabled ? 'LLM' : 'Deterministic';
  }

  criteriaThreshold(source: Pick<ScrapingSource, 'llm_fallback_enabled'> | ScrapingSourceCreateRequest): string {
    return source.llm_fallback_enabled ? '0.80' : '0.90';
  }

  criteriaChecks(source: Pick<ScrapingSource, 'llm_fallback_enabled'> | ScrapingSourceCreateRequest): string[] {
    if (source.llm_fallback_enabled) {
      return [
        'LLM says the page is an offer',
        'Offer type is resolved',
        'Title is present',
        'Summary is present',
        'Title is not generic',
      ];
    }
    return [
      'Offer type is resolved by the classifier',
      'Title is present',
      'Summary is present',
      'Summary is not fallback text',
      'Title is not generic',
    ];
  }

  saveSource(): void {
    this.savingSource.set(true);
    this.errorMessage = '';
    const { organization_id, ...formWithoutOrg } = this.sourceForm;
    const payload = this.auth.isTeacher
      ? (formWithoutOrg as ScrapingSourceCreateRequest)
      : this.sourceForm;
    const obs = this.sourceModalTarget
      ? this.api.patchScrapingSource(this.sourceModalTarget.key, payload)
      : this.api.createScrapingSource(payload);
    obs.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.savingSource.set(false);
        this.showSourceModal = false;
        this.loadSources();
      },
      error: () => {
        this.savingSource.set(false);
        this.errorMessage = 'Failed to save source. Check all required fields.';
      },
    });
  }

  toggleSourceEnabled(key: string, enabled: boolean): void {
    this.api.patchScrapingSource(key, { enabled })
      .pipe(takeUntil(this.destroy$))
      .subscribe({ next: (s) => { this.sources = this.sources.map(x => x.key === key ? s : x); } });
  }

  toggleSourceAutoPublish(key: string, auto_publish_enabled: boolean): void {
    this.api.patchScrapingSource(key, { auto_publish_enabled })
      .pipe(takeUntil(this.destroy$))
      .subscribe({ next: (s) => { this.sources = this.sources.map(x => x.key === key ? s : x); } });
  }

  deleteSource(src: ScrapingSource): void {
    if (!confirm(`Delete source "${src.name}"?`)) return;
    this.deletingSource.set(src.key);
    this.api.deleteScrapingSource(src.key).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.deletingSource.set(null);
        this.sources = this.sources.filter(s => s.key !== src.key);
      },
      error: () => {
        this.deletingSource.set(null);
        this.errorMessage = `Failed to delete source "${src.name}".`;
      },
    });
  }

  emptySourceForm(): ScrapingSourceCreateRequest {
    return {
      name: '',
      url: '',
      organization_id: '',
      target_profile: 'student',
      country: '',
      domain_names: [],
      interval_minutes: 360,
      llm_fallback_enabled: true,
      enabled: true,
      crawl_depth: 1,
      crawl_max_pages: 25,
      crawl_match_patterns: [],
      crawl_exclude_patterns: [],
      auto_publish_enabled: false,
      auto_publish_mode: 'llm',
    };
  }
}
