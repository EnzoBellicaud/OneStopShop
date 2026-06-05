import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ScrapperAdminPageComponent } from './scrapper-admin-page.component';
import { AuthService } from '../shared/auth.service';
import { environment } from '../../environments/environment';

const API = environment.apiBaseUrl;

function makeSource(key = 'src_a', overrides: Record<string, unknown> = {}) {
  return {
    key, name: `Source ${key}`, url: 'https://example.com',
    organization_token: 'org', offer_type: 'training',
    target_profile: 'student', country: 'IT',
    domain_names: [], interval_minutes: 360,
    llm_fallback_enabled: true, enabled: true,
    quality: 'real', crawl_enabled: false,
    crawl_depth: 1, crawl_max_pages: 25,
    crawl_match_patterns: [], crawl_exclude_patterns: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('ScrapperAdminPageComponent — Manage Sources tab', () => {
  let fixture: ComponentFixture<ScrapperAdminPageComponent>;
  let component: ScrapperAdminPageComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ScrapperAdminPageComponent, HttpClientTestingModule, RouterTestingModule],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: { get: () => null } } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ScrapperAdminPageComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);

    // Set admin so TABS includes 'manage'
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = true;
    auth.currentUser = { username: 'admin', email: 'a@a.com', profile: 'Admin' };

    fixture.detectChanges();
    // flush initial overview load
    http.match(() => true).forEach(r => {
      try { r.flush({}); } catch { /* ignore */ }
    });
  });

  afterEach(() => {
    http.verify();
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = false;
    auth.currentUser = null;
  });

  // ── TABS ──────────────────────────────────────────────────────────────────

  it('includes Manage Sources tab for admin', () => {
    const ids = component.TABS.map(t => t.id);
    expect(ids).toContain('manage');
  });

  // ── loadManagedSources ────────────────────────────────────────────────────

  it('loadManagedSources populates managedSources', () => {
    component.loadManagedSources();
    const req = http.expectOne(`${API}/admin/sources`);
    req.flush({ count: 2, results: [makeSource('a'), makeSource('b')] });
    expect(component.managedSources.length).toBe(2);
    expect(component.managedSources[0].key).toBe('a');
    expect(component.loadingManagedSources).toBeFalse();
  });

  it('loadManagedSources clears loading on error', () => {
    component.loadManagedSources();
    http.expectOne(`${API}/admin/sources`).error(new ProgressEvent('error'));
    expect(component.loadingManagedSources).toBeFalse();
  });

  // ── openCreateSource / openEditSource ─────────────────────────────────────

  it('openCreateSource opens modal in create mode', () => {
    component.openCreateSource();
    expect(component.showSourceModal).toBeTrue();
    expect(component.sourceModalTarget).toBeNull();
    expect(component.sourceForm.key).toBe('');
  });

  it('openEditSource prefills form with source data', () => {
    const src = makeSource('edit_me', { name: 'My Source', country: 'DE', llm_fallback_enabled: false });
    component.openEditSource(src as any);
    expect(component.showSourceModal).toBeTrue();
    expect(component.sourceModalTarget).toBe(src as any);
    expect(component.sourceForm.name).toBe('My Source');
    expect(component.sourceForm.country).toBe('DE');
    expect(component.sourceForm.llm_fallback_enabled).toBeFalse();
  });

  it('closeSourceModal hides modal', () => {
    component.showSourceModal = true;
    component.closeSourceModal();
    expect(component.showSourceModal).toBeFalse();
  });

  // ── saveSource ────────────────────────────────────────────────────────────

  it('saveSource POSTs when no sourceModalTarget (create mode)', () => {
    component.sourceModalTarget = null;
    component.sourceForm = {
      key: 'new_src', name: 'New', url: 'https://n.com',
      organization_token: 'o', offer_type: 'training', target_profile: 'student',
      country: 'IT', domain_names: [], interval_minutes: 360,
      llm_fallback_enabled: true, enabled: true, quality: 'real',
      crawl_enabled: false, crawl_depth: 1, crawl_max_pages: 25,
      crawl_match_patterns: [], crawl_exclude_patterns: [],
    };
    component.showSourceModal = true;
    component.saveSource();

    const req = http.expectOne(`${API}/admin/sources`);
    expect(req.request.method).toBe('POST');
    req.flush(makeSource('new_src'));

    // loadManagedSources is called after save
    http.expectOne(`${API}/admin/sources`).flush({ count: 1, results: [makeSource('new_src')] });

    expect(component.showSourceModal).toBeFalse();
    expect(component.savingSource()).toBeFalse();
  });

  it('saveSource PATCHes when sourceModalTarget set (edit mode)', () => {
    component.sourceModalTarget = makeSource('existing') as any;
    component.sourceForm = { ...component.emptySourceForm(), name: 'Updated' };
    component.showSourceModal = true;
    component.saveSource();

    const req = http.expectOne(`${API}/admin/sources/existing`);
    expect(req.request.method).toBe('PATCH');
    req.flush(makeSource('existing', { name: 'Updated' }));

    http.expectOne(`${API}/admin/sources`).flush({ count: 1, results: [makeSource('existing')] });

    expect(component.showSourceModal).toBeFalse();
  });

  // ── toggleLlmFallback / toggleSourceEnabled ───────────────────────────────

  it('toggleLlmFallback sends PATCH with llm_fallback_enabled', () => {
    component.managedSources = [makeSource('s1') as any];
    component.toggleLlmFallback('s1', false);

    const req = http.expectOne(`${API}/admin/sources/s1`);
    expect(req.request.body).toEqual({ llm_fallback_enabled: false });
    req.flush(makeSource('s1', { llm_fallback_enabled: false }));

    expect(component.managedSources[0].llm_fallback_enabled).toBeFalse();
  });

  it('toggleSourceEnabled sends PATCH with enabled', () => {
    component.managedSources = [makeSource('s2') as any];
    component.toggleSourceEnabled('s2', false);

    const req = http.expectOne(`${API}/admin/sources/s2`);
    expect(req.request.body).toEqual({ enabled: false });
    req.flush(makeSource('s2', { enabled: false }));

    expect(component.managedSources[0].enabled).toBeFalse();
  });

  // ── deleteSource ──────────────────────────────────────────────────────────

  it('deleteSource sends DELETE and removes from list', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    component.managedSources = [makeSource('to_delete') as any];
    component.deleteSource('to_delete');

    const req = http.expectOne(`${API}/admin/sources/to_delete`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(component.managedSources.length).toBe(0);
    expect(component.deletingSource()).toBeNull();
  });

  it('deleteSource does nothing when confirm returns false', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    component.managedSources = [makeSource('kept') as any];
    component.deleteSource('kept');

    http.expectNone(`${API}/admin/sources/kept`);
    expect(component.managedSources.length).toBe(1);
  });
});
