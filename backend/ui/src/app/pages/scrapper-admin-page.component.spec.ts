import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ScrapperAdminPageComponent } from './scrapper-admin-page.component';
import { AuthService } from '../shared/auth.service';

describe('ScrapperAdminPageComponent', () => {
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

    const auth = TestBed.inject(AuthService);
    auth.loggedIn = true;
    auth.currentUser = { username: 'admin', email: 'a@a.com', profile: 'Admin' };

    fixture.detectChanges();
    http.match(() => true).forEach(r => {
      try {
        const url = r.request.url;
        if (url.includes('/runs') || url.includes('/sources') || url.includes('/health')) {
          r.flush({ count: 0, results: [] });
        } else {
          r.flush({});
        }
      } catch { /* ignore */ }
    });
  });

  afterEach(() => {
    http.verify();
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = false;
    auth.currentUser = null;
  });

  it('has 4 tabs: overview, runs, sources, errors', () => {
    const ids = component.TABS.map(t => t.id);
    expect(ids).toEqual(['overview', 'runs', 'sources', 'errors']);
  });

  it('does not include a manage tab', () => {
    const ids: string[] = component.TABS.map(t => t.id);
    expect(ids).not.toContain('manage');
  });

  it('defaults to overview tab', () => {
    expect(component.activeTab()).toBe('overview');
  });

  it('selectTab changes active tab', () => {
    component.selectTab('runs');
    expect(component.activeTab()).toBe('runs');
    // flush runs request triggered by tab switch (must have results array)
    http.match(() => true).forEach(r => {
      try { r.flush({ count: 0, results: [] }); } catch { /* ignore */ }
    });
  });
});
