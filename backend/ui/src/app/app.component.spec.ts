import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { AuthService } from './shared/auth.service';

describe('AppComponent', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [AppComponent, HttpClientTestingModule, RouterTestingModule],
    }).compileComponents();
  });

  afterEach(() => {
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = false;
    auth.currentUser = null;
    localStorage.clear();
  });

  const enableLoggedInState = (): void => {
    const auth = TestBed.inject(AuthService);
    auth.loggedIn = true;
    auth.currentUser = { username: 'tester', email: 'tester@example.com', profile: 'Admin' };
  };

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it(`should have the 'SUNRISE OSS' title`, () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual('SUNRISE OSS');
  });

  it('should render navigation links', () => {
    enableLoggedInState();
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('a[href="/offers"]')?.textContent).toContain('Offers');
    expect(compiled.querySelector('a[href="/admin/scrapper"]')?.textContent).toContain('Scrapper Tracking');
  });
});
