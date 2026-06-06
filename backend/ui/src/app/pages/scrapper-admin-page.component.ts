import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, forkJoin, interval, of } from 'rxjs';
import { switchMap, startWith, takeUntil } from 'rxjs/operators';
import {
  LlmStats,
  ScrapingOverview,
  ScrapingRunDetail,
  ScrapingRunSummary,
  ScrapingSource,
  ScrapingSourceCreateRequest,
  SourceHealth,
} from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';
import { AuthService } from '../shared/auth.service';
import { parseRunLog, toUrlResults, RunLogEntry, UrlResult } from '../shared/run-log.parser';
import { StatCardComponent } from '../shared/components/stat-card.component';
import { MiniBarChartComponent, BarChartPoint } from '../shared/components/mini-bar-chart.component';
import { StatusChipComponent } from '../shared/components/status-chip.component';

type TabId = 'overview' | 'runs' | 'sources' | 'errors' | 'manage';
type WindowOption = '24h' | '7d' | '30d';

@Component({
  selector: 'app-scrapper-admin-page',
  standalone: true,
  imports: [CommonModule, FormsModule, StatCardComponent, MiniBarChartComponent, StatusChipComponent],
  templateUrl: './scrapper-admin-page.component.html',
  styleUrl: './scrapper-admin-page.component.css',
})
export class ScrapperAdminPageComponent implements OnInit, OnDestroy {
  get TABS(): { id: TabId; label: string }[] {
    const base: { id: TabId; label: string }[] = [
      { id: 'overview', label: 'Overview' },
      { id: 'runs', label: 'Runs' },
      { id: 'sources', label: 'Queue' },
      { id: 'errors', label: 'Errors' },
    ];
    if (this.auth.isAdmin) base.push({ id: 'manage', label: 'Manage Sources' });
    return base;
  }

  readonly WINDOWS: WindowOption[] = ['24h', '7d', '30d'];

  readonly SOURCE_SORTS: { id: 'name' | 'last_scraped' | 'pending' | 'done'; label: string }[] = [
    { id: 'name', label: 'Name' },
    { id: 'last_scraped', label: 'Last scraped' },
    { id: 'pending', label: 'Pending' },
    { id: 'done', label: 'Done' },
  ];


  readonly activeTab = signal<TabId>('overview');
  readonly autoRefresh = signal(true);
  lastRefreshed = new Date();

  // Overview
  overview: ScrapingOverview | null = null;
  overviewLlm: LlmStats | null = null;
  overviewWindow: WindowOption = '24h';
  loadingOverview = false;

  // Runs
  runs: ScrapingRunSummary[] = [];
  selectedRun: ScrapingRunDetail | null = null;
  limit = 20;
  sourceFilter = '';
  statusFilter = '';
  pinFailures = false;
  loadingRuns = false;
  loadingDetail = false;
  runUrlFilter: 'all' | 'failures' | 'skipped' = 'all';
  runSortCol: keyof UrlResult = 'url';
  runSortAsc = true;
  expandedRawRows = new Set<string>();

  // Sources
  sources: SourceHealth[] = [];
  sourceSort: 'name' | 'last_scraped' | 'pending' | 'done' = 'name';
  loadingSources = false;

  // Errors (cross-run, client-side aggregate)
  errorRuns: ScrapingRunDetail[] = [];
  loadingErrors = false;

  // Manage Sources
  managedSources: ScrapingSource[] = [];
  loadingManagedSources = false;
  sourceModalTarget: ScrapingSource | null = null;
  showSourceModal = false;
  savingSource = signal(false);
  deletingSource = signal<string | null>(null);
  sourceForm: ScrapingSourceCreateRequest = this.emptySourceForm();

  errorMessage = '';

  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly api: OssApiService,
    readonly auth: AuthService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    const tab = params.get('tab') as TabId | null;
    if (tab && this.TABS.some((t) => t.id === tab)) {
      this.activeTab.set(tab);
    }
    const sourceParam = params.get('source');
    if (sourceParam) this.sourceFilter = sourceParam;

    window.addEventListener('keydown', this.onKeyDown);

    interval(30_000)
      .pipe(startWith(0), takeUntil(this.destroy$))
      .subscribe(() => {
        if (this.autoRefresh()) this.loadCurrentTab();
      });

    const runId = params.get('run');
    if (runId && this.activeTab() === 'runs') {
      this.loadRuns().then(() => this.selectRun(runId));
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('keydown', this.onKeyDown);
  }

  private readonly onKeyDown = (e: KeyboardEvent): void => {
    const tag = (e.target as HTMLElement).tagName;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;
    if (e.key === 'r') this.refresh();
    const idx = parseInt(e.key) - 1;
    if (idx >= 0 && idx < this.TABS.length) this.selectTab(this.TABS[idx].id);
  };

  selectTab(tab: TabId): void {
    this.activeTab.set(tab);
    void this.router.navigate([], {
      queryParams: { tab },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    this.loadCurrentTab();
  }

  refresh(): void {
    this.loadCurrentTab();
  }

  toggleAutoRefresh(): void {
    this.autoRefresh.set(!this.autoRefresh());
  }

  private loadCurrentTab(): void {
    const tab = this.activeTab();
    this.lastRefreshed = new Date();
    if (tab === 'overview') this.loadOverview();
    else if (tab === 'runs') void this.loadRuns();
    else if (tab === 'sources') this.loadSources();
    else if (tab === 'errors') this.loadErrors();
    else if (tab === 'manage') this.loadManagedSources();
  }

  // ── Overview ──────────────────────────────────────────────────────────────

  loadOverview(): void {
    this.loadingOverview = true;
    let overviewDone = false;
    let llmDone = false;

    const tryFinish = () => {
      if (overviewDone && llmDone) this.loadingOverview = false;
    };

    this.api.getScrapingOverview(this.overviewWindow)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (overview) => { this.overview = overview; overviewDone = true; tryFinish(); },
        error: () => { overviewDone = true; tryFinish(); },
      });

    this.api.getLlmStats(this.overviewWindow)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (llm) => { this.overviewLlm = llm; llmDone = true; tryFinish(); },
        error: () => { llmDone = true; tryFinish(); },
      });
  }

  changeOverviewWindow(w: WindowOption): void {
    this.overviewWindow = w;
    this.loadOverview();
  }

  get timelineRunChart(): BarChartPoint[] {
    return (this.overview?.runs_timeline ?? []).map((b) => ({
      value: b.runs,
      label: this.formatBucket(b.bucket),
    }));
  }

  get timelineErrorChart(): BarChartPoint[] {
    return (this.overview?.runs_timeline ?? []).map((b) => ({
      value: b.errors,
      label: this.formatBucket(b.bucket),
    }));
  }

  private formatBucket(bucket: string): string {
    // backend returns "2025-04-25T14:00:00Z" (24h) or "2025-04-25" (7d/30d)
    if (this.overviewWindow === '24h') {
      const h = bucket.length >= 16 ? bucket.substring(11, 16) : bucket;
      return h;
    }
    // "2025-04-25" → "Apr 25"
    const parts = bucket.substring(0, 10).split('-');
    if (parts.length < 3) return bucket;
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const m = parseInt(parts[1], 10) - 1;
    return `${months[m] ?? parts[1]} ${parseInt(parts[2], 10)}`;
  }

  get overviewConfLlm(): string {
    const v = this.overviewLlm?.avg_confidence_llm;
    return v != null ? v.toFixed(2) : '—';
  }

  get overviewConfDet(): string {
    const v = this.overviewLlm?.avg_confidence_deterministic;
    return v != null ? v.toFixed(2) : '—';
  }

  get overviewMethodSplit(): { method: string; count: number; pct: number }[] {
    if (!this.overviewLlm) return [];
    const split = this.overviewLlm.method_split;
    const total = Object.values(split).reduce((a, b) => a + b, 0) || 1;
    return Object.entries(split).map(([method, count]) => ({
      method,
      count,
      pct: Math.round((count / total) * 100),
    }));
  }

  // ── Runs ──────────────────────────────────────────────────────────────────

  async loadRuns(): Promise<void> {
    this.loadingRuns = true;
    return new Promise((resolve) => {
      this.api
        .getScrapingRuns(this.limit)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (payload) => {
            this.runs = payload.results;
            this.loadingRuns = false;
            if (!this.selectedRun && this.runs.length > 0) {
              this.selectRun(this.runs[0].id);
            }
            resolve();
          },
          error: () => {
            this.loadingRuns = false;
            resolve();
          },
        });
    });
  }

  refreshRuns(): void {
    void this.loadRuns();
  }

  selectRun(runId: string): void {
    this.loadingDetail = true;
    this.expandedRawRows.clear();
    void this.router.navigate([], {
      queryParams: { run: runId },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    this.api
      .getScrapingRunDetail(runId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (payload) => {
          this.selectedRun = payload;
          this.loadingDetail = false;
        },
        error: () => {
          this.selectedRun = null;
          this.loadingDetail = false;
        },
      });
  }

  get filteredRuns(): ScrapingRunSummary[] {
    let result = this.runs.filter((r) => {
      const statusOk = this.statusFilter ? r.status === this.statusFilter : true;
      const sourceOk = this.sourceFilter
        ? r.source_key.toLowerCase().includes(this.sourceFilter.toLowerCase())
        : true;
      return statusOk && sourceOk;
    });
    if (this.pinFailures) {
      result = [
        ...result.filter((r) => r.status === 'failed'),
        ...result.filter((r) => r.status !== 'failed'),
      ];
    }
    return result;
  }

  get statuses(): string[] {
    return Array.from(new Set(this.runs.map((r) => r.status))).sort();
  }

  get selectedRunEntries(): RunLogEntry[] {
    return this.selectedRun ? parseRunLog(this.selectedRun.log) : [];
  }

  get selectedRunUrlResults(): UrlResult[] {
    let results = toUrlResults(this.selectedRunEntries);
    if (this.runUrlFilter === 'failures') results = results.filter((r) => r.failed);
    if (this.runUrlFilter === 'skipped') results = results.filter((r) => r.neglected);
    const NUMERIC_COLS: Array<keyof UrlResult> = ['http_status', 'confidence', 'duration_ms'];
    return [...results].sort((a, b) => {
      const col = this.runSortCol;
      let cmp: number;
      if (NUMERIC_COLS.includes(col)) {
        const an = a[col] as number | null ?? -Infinity;
        const bn = b[col] as number | null ?? -Infinity;
        cmp = an - bn;
      } else {
        const av = String(a[col] ?? '');
        const bv = String(b[col] ?? '');
        cmp = av.localeCompare(bv);
      }
      return this.runSortAsc ? cmp : -cmp;
    });
  }

  sortRunResults(col: keyof UrlResult): void {
    if (this.runSortCol === col) this.runSortAsc = !this.runSortAsc;
    else { this.runSortCol = col; this.runSortAsc = true; }
  }

  toggleRawRow(url: string): void {
    this.expandedRawRows.has(url)
      ? this.expandedRawRows.delete(url)
      : this.expandedRawRows.add(url);
  }

  exportRunCsv(): void {
    const results = this.selectedRunUrlResults;
    if (!results.length) return;
    const header = 'url,method,http_status,confidence,failed,action,reason,message';
    const rows = results.map((r) =>
      [r.url, r.method, r.http_status, r.confidence, r.failed, r.action, r.reason, r.message]
        .map((v) => (v == null ? '' : `"${String(v).replace(/"/g, '""')}"`))
        .join(','),
    );
    const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `run-${this.selectedRun?.id ?? 'export'}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  trackRun(_i: number, run: ScrapingRunSummary): string {
    return run.id;
  }

  relativeTime(dateStr: string | null): string {
    if (!dateStr) return 'n/a';
    const diff = Date.now() - new Date(dateStr).getTime();
    if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`;
    if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.round(diff / 3_600_000)}h ago`;
    return `${Math.round(diff / 86_400_000)}d ago`;
  }

  // ── Sources ───────────────────────────────────────────────────────────────

  loadSources(): void {
    this.loadingSources = true;
    this.api
      .getSourcesHealth()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (payload) => {
          this.sources = payload.results;
          this.loadingSources = false;
        },
        error: () => {
          this.loadingSources = false;
        },
      });
  }

  get sortedSources(): SourceHealth[] {
    return [...this.sources].sort((a, b) => {
      if (this.sourceSort === 'name') return a.source_key.localeCompare(b.source_key);
      if (this.sourceSort === 'last_scraped') {
        return (b.last_scraped_at ?? '').localeCompare(a.last_scraped_at ?? '');
      }
      if (this.sourceSort === 'pending') return b.pending - a.pending;
      if (this.sourceSort === 'done') return b.done - a.done;
      return 0;
    });
  }

  sourceDonePercent(source: SourceHealth): number {
    if (!source.total_urls) return 0;
    return Math.round((source.done / source.total_urls) * 100);
  }

  viewSourceRuns(sourceKey: string): void {
    this.sourceFilter = sourceKey;
    this.selectTab('runs');
  }

  // ── Manage Sources ────────────────────────────────────────────────────────

  loadManagedSources(): void {
    this.loadingManagedSources = true;
    this.api.getScrapingSources().pipe(takeUntil(this.destroy$)).subscribe({
      next: (res) => { this.managedSources = res.results; this.loadingManagedSources = false; },
      error: () => { this.loadingManagedSources = false; },
    });
  }

  openCreateSource(): void {
    this.sourceModalTarget = null;
    this.sourceForm = this.emptySourceForm();
    this.showSourceModal = true;
  }

  openEditSource(src: ScrapingSource): void {
    this.sourceModalTarget = src;
    this.sourceForm = {
      key: src.key, name: src.name, url: src.url,
      organization_token: src.organization_token,
      target_profile: src.target_profile,
      country: src.country, domain_names: [...src.domain_names],
      interval_minutes: src.interval_minutes,
      llm_fallback_enabled: src.llm_fallback_enabled,
      enabled: src.enabled, quality: src.quality,
      crawl_enabled: src.crawl_enabled, crawl_depth: src.crawl_depth,
      crawl_max_pages: src.crawl_max_pages,
      crawl_match_patterns: [...src.crawl_match_patterns],
      crawl_exclude_patterns: [...src.crawl_exclude_patterns],
    };
    this.showSourceModal = true;
  }

  closeSourceModal(): void {
    this.showSourceModal = false;
  }

  saveSource(): void {
    this.savingSource.set(true);
    const obs = this.sourceModalTarget
      ? this.api.patchScrapingSource(this.sourceModalTarget.key, this.sourceForm)
      : this.api.createScrapingSource(this.sourceForm);
    obs.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.savingSource.set(false);
        this.showSourceModal = false;
        this.loadManagedSources();
      },
      error: () => { this.savingSource.set(false); this.errorMessage = 'Failed to save source. Check all required fields.'; },
    });
  }

  toggleSourceEnabled(key: string, enabled: boolean): void {
    this.api.patchScrapingSource(key, { enabled })
      .pipe(takeUntil(this.destroy$))
      .subscribe({ next: (s) => { this.managedSources = this.managedSources.map(x => x.key === key ? s : x); } });
  }

  deleteSource(key: string): void {
    if (!confirm(`Delete source "${key}"?`)) return;
    this.deletingSource.set(key);
    this.api.deleteScrapingSource(key).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.deletingSource.set(null);
        this.managedSources = this.managedSources.filter(s => s.key !== key);
      },
      error: () => { this.deletingSource.set(null); this.errorMessage = `Failed to delete source "${key}".`; },
    });
  }

  emptySourceForm(): ScrapingSourceCreateRequest {
    return {
      key: '', name: '', url: '', organization_token: '',
      target_profile: 'student',
      country: '', domain_names: [], interval_minutes: 360,
      llm_fallback_enabled: true, enabled: true, quality: 'real',
      crawl_enabled: false, crawl_depth: 1, crawl_max_pages: 25,
      crawl_match_patterns: [], crawl_exclude_patterns: [],
    };
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  friendlyMethod(method: string): string {
    const names: Record<string, string> = {
      llm_primary: 'AI (primary)',
      llm_fallback: 'AI (fallback)',
      deterministic: 'Rules-based',
    };
    return names[method] ?? method;
  }

  formatSourceKey(key: string): string {
    if (key.startsWith('import__')) {
      const suffix = key.slice(8);
      return `Manual Import · ${suffix.length > 12 ? suffix.slice(0, 8) + '…' : suffix}`;
    }
    return key;
  }

  // ── Errors ────────────────────────────────────────────────────────────────

  loadErrors(): void {
    this.loadingErrors = true;
    this.api
      .getScrapingRuns(50)
      .pipe(
        takeUntil(this.destroy$),
        switchMap(({ results }) =>
          results.length
            ? forkJoin(results.map((r) => this.api.getScrapingRunDetail(r.id)))
            : of([] as ScrapingRunDetail[]),
        ),
      )
      .subscribe({
        next: (details) => {
          this.errorRuns = details;
          this.loadingErrors = false;
        },
        error: () => {
          this.loadingErrors = false;
        },
      });
  }

  get crossRunErrors(): {
    ts?: string;
    source_key?: string;
    url?: string;
    http_status?: number;
    message?: string;
    runId: string;
  }[] {
    const errors: {
      ts?: string;
      source_key?: string;
      url?: string;
      http_status?: number;
      message?: string;
      runId: string;
    }[] = [];
    for (const run of this.errorRuns) {
      for (const entry of parseRunLog(run.log)) {
        if (entry.event === 'url_failed' && entry.level !== 'info') {
          errors.push({
            ts: entry.ts,
            source_key: entry.source_key,
            url: entry.url,
            http_status: entry.http_status,
            message: entry.message ?? entry.reason,
            runId: run.id,
          });
        }
      }
    }
    return errors.sort((a, b) => (b.ts ?? '').localeCompare(a.ts ?? ''));
  }

  openRunFromError(runId: string): void {
    this.selectTab('runs');
    this.selectRun(runId);
  }
}
