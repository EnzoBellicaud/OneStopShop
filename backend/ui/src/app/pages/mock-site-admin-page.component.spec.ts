import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockSiteAdminPageComponent } from './mock-site-admin-page.component';
import { environment } from '../../environments/environment';

const API = environment.apiBaseUrl;

function makeOpp(overrides: Record<string, unknown> = {}) {
  return {
    id: 'aaaaaaaa-0000-0000-0000-000000000001',
    title: 'Python Internship Program',
    description: 'A great internship for CS students.',
    offer_type: 'internship',
    target_profile: 'student',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('MockSiteAdminPageComponent', () => {
  let fixture: ComponentFixture<MockSiteAdminPageComponent>;
  let component: MockSiteAdminPageComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MockSiteAdminPageComponent, HttpClientTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(MockSiteAdminPageComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  // ── ngOnInit ──────────────────────────────────────────────────────────────

  it('loads opportunities on init', () => {
    const opps = [makeOpp(), makeOpp({ id: 'aaaaaaaa-0000-0000-0000-000000000002', title: 'Thesis B' })];
    fixture.detectChanges();

    const req = http.expectOne(`${API}/admin/mock-opportunities`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 2, results: opps });

    expect(component.mockOpportunities.length).toBe(2);
    expect(component.loadingMock).toBeFalse();
  });

  it('clears loadingMock on error', () => {
    fixture.detectChanges();
    http.expectOne(`${API}/admin/mock-opportunities`).error(new ProgressEvent('error'));
    expect(component.loadingMock).toBeFalse();
  });

  // ── openAddOpportunity ────────────────────────────────────────────────────

  it('openAddOpportunity resets form and shows modal', () => {
    component.mockForm = { title: 'Old', description: 'Old', offer_type: 'thesis', target_profile: 'teacher' };
    component.openAddOpportunity();
    expect(component.showMockModal).toBeTrue();
    expect(component.mockForm.title).toBe('');
    expect(component.mockForm.offer_type).toBe('internship');
    expect(component.mockForm.target_profile).toBe('student');
    expect(component.mockError).toBeNull();
  });

  // ── closeMockModal ────────────────────────────────────────────────────────

  it('closeMockModal hides modal', () => {
    component.showMockModal = true;
    component.closeMockModal();
    expect(component.showMockModal).toBeFalse();
  });

  // ── saveOpportunity ───────────────────────────────────────────────────────

  it('saveOpportunity POSTs and reloads list', () => {
    fixture.detectChanges();
    http.expectOne(`${API}/admin/mock-opportunities`).flush({ count: 0, results: [] });

    component.mockForm = {
      title: 'New Internship',
      description: 'desc',
      offer_type: 'internship',
      target_profile: 'student',
    };
    component.showMockModal = true;
    component.saveOpportunity();

    const postReq = http.expectOne(`${API}/admin/mock-opportunities`);
    expect(postReq.request.method).toBe('POST');
    expect(postReq.request.body.title).toBe('New Internship');
    postReq.flush(makeOpp({ title: 'New Internship' }));

    const reloadReq = http.expectOne(`${API}/admin/mock-opportunities`);
    reloadReq.flush({ count: 1, results: [makeOpp({ title: 'New Internship' })] });

    expect(component.showMockModal).toBeFalse();
    expect(component.savingMock).toBeFalse();
    expect(component.mockOpportunities.length).toBe(1);
  });

  it('saveOpportunity sets error when title is blank', () => {
    component.mockForm.title = '   ';
    component.saveOpportunity();
    expect(component.mockError).toBeTruthy();
    http.expectNone(`${API}/admin/mock-opportunities`);
  });

  it('saveOpportunity sets error on API failure', () => {
    fixture.detectChanges();
    http.expectOne(`${API}/admin/mock-opportunities`).flush({ count: 0, results: [] });

    component.mockForm = { title: 'Fail', description: '', offer_type: 'internship', target_profile: 'student' };
    component.saveOpportunity();

    http.expectOne(`${API}/admin/mock-opportunities`).error(new ProgressEvent('error'));

    expect(component.mockError).toBeTruthy();
    expect(component.savingMock).toBeFalse();
  });

  // ── deleteOpportunity ─────────────────────────────────────────────────────

  it('deleteOpportunity sends DELETE and removes item from list', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    component.mockOpportunities = [makeOpp() as any];

    component.deleteOpportunity('aaaaaaaa-0000-0000-0000-000000000001');

    const req = http.expectOne(`${API}/admin/mock-opportunities/aaaaaaaa-0000-0000-0000-000000000001`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(component.mockOpportunities.length).toBe(0);
    expect(component.deletingMock).toBeNull();
  });

  it('deleteOpportunity does nothing when confirm returns false', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    component.mockOpportunities = [makeOpp() as any];

    component.deleteOpportunity('aaaaaaaa-0000-0000-0000-000000000001');

    http.expectNone(`${API}/admin/mock-opportunities/aaaaaaaa-0000-0000-0000-000000000001`);
    expect(component.mockOpportunities.length).toBe(1);
  });

  it('deleteOpportunity clears deletingMock on error', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    component.mockOpportunities = [makeOpp() as any];
    component.deleteOpportunity('aaaaaaaa-0000-0000-0000-000000000001');

    http.expectOne(`${API}/admin/mock-opportunities/aaaaaaaa-0000-0000-0000-000000000001`)
      .error(new ProgressEvent('error'));

    expect(component.deletingMock).toBeNull();
    expect(component.mockOpportunities.length).toBe(1);
  });

  // ── initial state ─────────────────────────────────────────────────────────

  it('initial state has empty list and modal closed', () => {
    expect(component.mockOpportunities).toEqual([]);
    expect(component.showMockModal).toBeFalse();
    expect(component.savingMock).toBeFalse();
    expect(component.deletingMock).toBeNull();
  });
});
