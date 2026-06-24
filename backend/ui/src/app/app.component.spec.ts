import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { AuthService } from './shared/auth.service';
import { environment } from '../environments/environment';

describe('AppComponent', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [AppComponent, HttpClientTestingModule, RouterTestingModule],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = false;
    auth.currentUser = null;
    localStorage.clear();
    http.verify();
  });

  const enableAdmin = (): void => {
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = true;
    auth.currentUser = { username: 'tester', email: 'tester@example.com', profile: 'Admin' };
  };

  const enableTeacher = (): void => {
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = true;
    auth.currentUser = { username: 'teacher', email: 'teacher@example.com', profile: 'Teacher' };
  };

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should have SUNRISE OSS title', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance.title).toEqual('SUNRISE OSS');
  });

  it('should render nav links when logged in', () => {
    enableAdmin();
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    http.match(() => true).forEach(r => r.flush({ count: 0, results: [] }));
    const el = fixture.nativeElement as HTMLElement;
    const hrefs = Array.from(el.querySelectorAll('a')).map(a => a.getAttribute('href'));
    expect(hrefs).toContain('/offers');
    expect(hrefs).toContain('/admin/scrapper');
    expect(hrefs).toContain('/admin/users');
  });

  it('Teacher user sees Sources nav link', () => {
    enableTeacher();
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    http.match(() => true).forEach(r => r.flush({ count: 0, results: [] }));
    const el = fixture.nativeElement as HTMLElement;
    const hrefs = Array.from(el.querySelectorAll('a')).map(a => a.getAttribute('href'));
    expect(hrefs).toContain('/admin/sources');
  });

  it('Teacher user does not see admin-only nav links', () => {
    enableTeacher();
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    http.match(() => true).forEach(r => r.flush({ count: 0, results: [] }));
    const el = fixture.nativeElement as HTMLElement;
    const hrefs = Array.from(el.querySelectorAll('a')).map(a => a.getAttribute('href'));
    expect(hrefs).not.toContain('/admin/users');
    expect(hrefs).not.toContain('/admin/organizations');
  });

  // ── Change password modal ──────────────────────────────────────────────

  describe('change password', () => {
    it('showChangePw defaults to false', () => {
      const fixture = TestBed.createComponent(AppComponent);
      expect(fixture.componentInstance.showChangePw).toBeFalse();
    });

    it('submitChangePassword sets error when passwords do not match', () => {
      const fixture = TestBed.createComponent(AppComponent);
      const comp = fixture.componentInstance;
      comp.changePwForm = { old_password: 'old', new_password: 'newpass1', confirm: 'newpass2' };
      comp.submitChangePassword();
      expect(comp.changePwError()).toBe('New passwords do not match.');
    });

    it('submitChangePassword sets error when new password too short', () => {
      const fixture = TestBed.createComponent(AppComponent);
      const comp = fixture.componentInstance;
      comp.changePwForm = { old_password: 'old', new_password: 'short', confirm: 'short' };
      comp.submitChangePassword();
      expect(comp.changePwError()).toBe('New password must be at least 8 characters.');
    });

    it('submitChangePassword calls API and sets success', () => {
      const fixture = TestBed.createComponent(AppComponent);
      const comp = fixture.componentInstance;
      comp.changePwForm = { old_password: 'OldPass1!', new_password: 'NewPass1!', confirm: 'NewPass1!' };
      comp.submitChangePassword();

      const req = http.expectOne(`${environment.apiBaseUrl}/auth/change-password`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body.old_password).toBe('OldPass1!');
      expect(req.request.body.new_password).toBe('NewPass1!');
      req.flush({ detail: 'Password changed successfully' });

      expect(comp.changePwSuccess()).toBeTrue();
      expect(comp.submittingPw()).toBeFalse();
    });

    it('submitChangePassword sets API error on failure', () => {
      const fixture = TestBed.createComponent(AppComponent);
      const comp = fixture.componentInstance;
      comp.changePwForm = { old_password: 'wrong', new_password: 'NewPass1!', confirm: 'NewPass1!' };
      comp.submitChangePassword();

      const req = http.expectOne(`${environment.apiBaseUrl}/auth/change-password`);
      req.flush({ detail: 'Incorrect current password.' }, { status: 400, statusText: 'Bad Request' });

      expect(comp.changePwSuccess()).toBeFalse();
      expect(comp.changePwError()).toBe('Incorrect current password.');
    });

    it('closeChangePw resets all state', () => {
      const fixture = TestBed.createComponent(AppComponent);
      const comp = fixture.componentInstance;
      comp.showChangePw = true;
      comp.changePwSuccess.set(true);
      comp.changePwError.set('some error');
      comp.changePwForm = { old_password: 'x', new_password: 'y', confirm: 'z' };

      comp.closeChangePw();

      expect(comp.showChangePw).toBeFalse();
      expect(comp.changePwSuccess()).toBeFalse();
      expect(comp.changePwError()).toBeNull();
      expect(comp.changePwForm.old_password).toBe('');
      expect(comp.changePwForm.new_password).toBe('');
      expect(comp.changePwForm.confirm).toBe('');
    });
  });
});
