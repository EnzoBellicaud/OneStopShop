import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SourcesAdminPageComponent } from './sources-admin-page.component';
import { AuthService } from '../shared/auth.service';
import { environment } from '../../environments/environment';

const API = environment.apiBaseUrl;

function makeSource(key = 'src_a', overrides: Record<string, unknown> = {}) {
  return {
    key, name: `Source ${key}`, url: 'https://example.com',
    organization_id: null,
    offer_type: 'training',
    target_profile: 'student', country: 'IT',
    domain_names: [], interval_minutes: 360,
    llm_fallback_enabled: true, enabled: true,
    quality: 'real',
    crawl_depth: 1, crawl_max_pages: 25,
    crawl_match_patterns: [], crawl_exclude_patterns: [],
    auto_publish_enabled: false,
    auto_publish_mode: 'llm',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('SourcesAdminPageComponent', () => {
  let fixture: ComponentFixture<SourcesAdminPageComponent>;
  let component: SourcesAdminPageComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SourcesAdminPageComponent, HttpClientTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(SourcesAdminPageComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);

    fixture.detectChanges();
    // flush both ngOnInit calls: getScrapingSources + getOrganizations
    http.expectOne(`${API}/admin/sources`).flush({ count: 0, results: [] });
    http.expectOne(`${API}/lookups/organizations`).flush({ count: 0, results: [] });
  });

  afterEach(() => {
    http.verify();
  });

  // ── loadSources ───────────────────────────────────────────────────────────

  it('loadSources populates sources', () => {
    component.loadSources();
    http.expectOne(`${API}/admin/sources`).flush({ count: 2, results: [makeSource('a'), makeSource('b')] });
    expect(component.sources.length).toBe(2);
    expect(component.sources[0].key).toBe('a');
    expect(component.loading).toBeFalse();
  });

  it('loadSources clears loading on error', () => {
    component.loadSources();
    http.expectOne(`${API}/admin/sources`).error(new ProgressEvent('error'));
    expect(component.loading).toBeFalse();
  });

  // ── openCreateSource / openEditSource ────────────────────────────────────

  it('openCreateSource opens modal in create mode', () => {
    component.openCreateSource();
    expect(component.showSourceModal).toBeTrue();
    expect(component.sourceModalTarget).toBeNull();
    expect(component.sourceForm.name).toBe('');
  });

  it('openEditSource prefills form with source data', () => {
    const src = makeSource('edit_me', { name: 'My Source', country: 'DE', llm_fallback_enabled: false });
    component.openEditSource(src as any);
    expect(component.showSourceModal).toBeTrue();
    expect(component.sourceModalTarget).toBe(src as any);
    expect(component.sourceForm.name).toBe('My Source');
    expect(component.sourceForm.country).toBe('DE');
    expect(component.sourceForm.llm_fallback_enabled).toBeFalse();
    expect(component.sourceForm.auto_publish_enabled).toBeFalse();
  });

  it('closeSourceModal hides modal', () => {
    component.showSourceModal = true;
    component.closeSourceModal();
    expect(component.showSourceModal).toBeFalse();
  });

  it('openCriteriaModal stores source and closeCriteriaModal clears it', () => {
    const src = makeSource('criteria') as any;
    component.openCriteriaModal(src);
    expect(component.criteriaModalSource).toBe(src);
    component.closeCriteriaModal();
    expect(component.criteriaModalSource).toBeNull();
  });

  it('criteria helpers return LLM criteria', () => {
    const src = makeSource('llm', { llm_fallback_enabled: true }) as any;
    expect(component.criteriaMode(src)).toBe('LLM');
    expect(component.criteriaThreshold(src)).toBe('0.80');
    expect(component.criteriaChecks(src)).toContain('LLM says the page is an offer');
  });

  it('criteria helpers return deterministic criteria', () => {
    const src = makeSource('det', { llm_fallback_enabled: false }) as any;
    expect(component.criteriaMode(src)).toBe('Deterministic');
    expect(component.criteriaThreshold(src)).toBe('0.90');
    expect(component.criteriaChecks(src)).toContain('Summary is not fallback text');
  });

  // ── saveSource ────────────────────────────────────────────────────────────

  it('saveSource POSTs when no sourceModalTarget (create mode)', () => {
    component.sourceModalTarget = null;
    component.sourceForm = {
      name: 'New', url: 'https://n.com',
      organization_id: '',
      target_profile: 'student',
      country: 'IT', domain_names: [], interval_minutes: 360,
      llm_fallback_enabled: true, enabled: true,
      crawl_depth: 1, crawl_max_pages: 25,
      crawl_match_patterns: [], crawl_exclude_patterns: [],
      auto_publish_enabled: false, auto_publish_mode: 'llm',
    };
    component.showSourceModal = true;
    component.saveSource();

    const req = http.expectOne(`${API}/admin/sources`);
    expect(req.request.method).toBe('POST');
    req.flush(makeSource('new_src'));

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

  // ── toggleSourceEnabled ───────────────────────────────────────────────────

  it('toggleSourceEnabled sends PATCH with enabled', () => {
    component.sources = [makeSource('s2') as any];
    component.toggleSourceEnabled('s2', false);

    const req = http.expectOne(`${API}/admin/sources/s2`);
    expect(req.request.body).toEqual({ enabled: false });
    req.flush(makeSource('s2', { enabled: false }));

    expect(component.sources[0].enabled).toBeFalse();
  });

  it('toggleSourceAutoPublish sends PATCH with auto_publish_enabled', () => {
    component.sources = [makeSource('s3') as any];
    component.toggleSourceAutoPublish('s3', true);

    const req = http.expectOne(`${API}/admin/sources/s3`);
    expect(req.request.body).toEqual({ auto_publish_enabled: true });
    req.flush(makeSource('s3', { auto_publish_enabled: true }));

    expect(component.sources[0].auto_publish_enabled).toBeTrue();
  });

  // ── deleteSource ──────────────────────────────────────────────────────────

  it('deleteSource sends DELETE and removes from list', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    component.sources = [makeSource('to_delete') as any];
    component.deleteSource(makeSource('to_delete') as any);

    const req = http.expectOne(`${API}/admin/sources/to_delete`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(component.sources.length).toBe(0);
    expect(component.deletingSource()).toBeNull();
  });

  it('deleteSource does nothing when confirm returns false', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    component.sources = [makeSource('kept') as any];
    component.deleteSource(makeSource('kept') as any);

    http.expectNone(`${API}/admin/sources/kept`);
    expect(component.sources.length).toBe(1);
  });
});

describe('SourcesAdminPageComponent — offer manager mode', () => {
  let fixture: ComponentFixture<SourcesAdminPageComponent>;
  let component: SourcesAdminPageComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SourcesAdminPageComponent, HttpClientTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(SourcesAdminPageComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);

    // Spy before detectChanges so ngOnInit sees the offer manager flags
    spyOnProperty(component.auth, 'isTeacher', 'get').and.returnValue(true);
    spyOnProperty(component.auth, 'isAdmin', 'get').and.returnValue(false);

    fixture.detectChanges();
    // Only sources request — getOrganizations is skipped for offer managers
    http.expectOne(`${API}/admin/sources`).flush({ count: 1, results: [makeSource('own_src')] });
  });

  afterEach(() => {
    http.verify();
  });

  it('hides org dropdown in modal for offer manager', () => {
    component.openCreateSource();
    fixture.detectChanges();
    const labels: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('label.form-field'));
    const orgLabel = labels.find(el => el.textContent?.includes('Organization'));
    expect(orgLabel).toBeUndefined();
  });

  it('saveSource create does not include organization_id in POST body', () => {
    component.sourceModalTarget = null;
    component.sourceForm = {
      name: 'OM Source', url: 'https://om.com',
      organization_id: 'should-be-stripped',
      target_profile: 'student', country: 'IT',
      domain_names: [], interval_minutes: 360,
      llm_fallback_enabled: true, enabled: true,
      crawl_depth: 1, crawl_max_pages: 25,
      crawl_match_patterns: [], crawl_exclude_patterns: [],
      auto_publish_enabled: false, auto_publish_mode: 'llm',
    };
    component.saveSource();

    const req = http.expectOne(`${API}/admin/sources`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.organization_id).toBeUndefined();
    req.flush(makeSource('om_src'));
    http.expectOne(`${API}/admin/sources`).flush({ count: 1, results: [makeSource('om_src')] });
  });

  it('saveSource patch does not include organization_id in PATCH body', () => {
    component.sourceModalTarget = makeSource('existing') as any;
    component.sourceForm = { ...component.emptySourceForm(), name: 'Updated', organization_id: 'should-be-stripped' };
    component.saveSource();

    const req = http.expectOne(`${API}/admin/sources/existing`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body.organization_id).toBeUndefined();
    req.flush(makeSource('existing', { name: 'Updated' }));
    http.expectOne(`${API}/admin/sources`).flush({ count: 1, results: [makeSource('existing')] });
  });
});
