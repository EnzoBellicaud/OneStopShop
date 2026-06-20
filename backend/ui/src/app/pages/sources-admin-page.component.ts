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
import { TranslatePipe } from '../shared/i18n/translate.pipe';

@Component({
  selector: 'app-sources-admin-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './sources-admin-page.component.html',
  styleUrl: './sources-admin-page.component.css',
})
export class SourcesAdminPageComponent implements OnInit, OnDestroy {
  sources: ScrapingSource[] = [];
  organizations: OrganizationLookup[] = [];
  loading = false;
  sourceModalTarget: ScrapingSource | null = null;
  showSourceModal = false;
  savingSource = signal(false);
  deletingSource = signal<string | null>(null);
  sourceForm: ScrapingSourceCreateRequest = this.emptySourceForm();
  errorMessage = '';

  private readonly destroy$ = new Subject<void>();

  constructor(private readonly api: OssApiService) {}

  ngOnInit(): void {
    this.loadSources();
    this.api.getOrganizations()
      .pipe(takeUntil(this.destroy$))
      .subscribe({ next: (res) => { this.organizations = res.results; } });
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
      key: src.key,
      name: src.name,
      url: src.url,
      organization_id: src.organization_id ?? '',
      target_profile: src.target_profile,
      country: src.country,
      domain_names: [...src.domain_names],
      interval_minutes: src.interval_minutes,
      llm_fallback_enabled: src.llm_fallback_enabled,
      enabled: src.enabled,
      quality: src.quality,
      crawl_depth: src.crawl_depth,
      crawl_max_pages: src.crawl_max_pages,
      crawl_match_patterns: [...src.crawl_match_patterns],
      crawl_exclude_patterns: [...src.crawl_exclude_patterns],
    };
    this.errorMessage = '';
    this.showSourceModal = true;
  }

  closeSourceModal(): void {
    this.showSourceModal = false;
    this.errorMessage = '';
  }

  saveSource(): void {
    this.savingSource.set(true);
    this.errorMessage = '';
    const obs = this.sourceModalTarget
      ? this.api.patchScrapingSource(this.sourceModalTarget.key, this.sourceForm)
      : this.api.createScrapingSource(this.sourceForm);
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

  deleteSource(key: string): void {
    if (!confirm(`Delete source "${key}"?`)) return;
    this.deletingSource.set(key);
    this.api.deleteScrapingSource(key).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.deletingSource.set(null);
        this.sources = this.sources.filter(s => s.key !== key);
      },
      error: () => {
        this.deletingSource.set(null);
        this.errorMessage = `Failed to delete source "${key}".`;
      },
    });
  }

  emptySourceForm(): ScrapingSourceCreateRequest {
    return {
      key: '',
      name: '',
      url: '',
      organization_id: '',
      target_profile: 'student',
      country: '',
      domain_names: [],
      interval_minutes: 360,
      llm_fallback_enabled: true,
      enabled: true,
      quality: 'real',
      crawl_depth: 1,
      crawl_max_pages: 25,
      crawl_match_patterns: [],
      crawl_exclude_patterns: [],
    };
  }
}
