import { Injectable } from '@angular/core';
import { HttpBackend, HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, map, tap } from 'rxjs';
import { Router } from '@angular/router';
import { environment } from '../../environments/environment';

interface LoginResponse {
  user: { id: string; username: string; email: string; profile: string };
  tokens: { access_token: string; refresh_token: string };
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'oss.access_token';
  private readonly REFRESH_KEY = 'oss.refresh_token';
  private readonly USER_KEY = 'oss.user';

  currentUser: { username: string; email: string; profile: string } | null = this.getUser();
  loggedIn = !!localStorage.getItem(this.TOKEN_KEY);

  constructor(
    private readonly http: HttpClient,
    private readonly httpBackend: HttpBackend,
    private readonly router: Router,
  ) {}

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiBaseUrl}/auth/login`, { username, password })
      .pipe(tap(res => this.storeSession(res)));
  }

  logout(): void {
    this.http.post(`${environment.apiBaseUrl}/auth/logout`, {}).subscribe({ error: () => {} });
    this.clearSession();
    this.router.navigate(['/login']);
  }

  forceLogout(): void {
    this.clearSession();
    this.router.navigate(['/login']);
  }

  get profile(): string | null {
    return this.currentUser?.profile ?? null;
  }

  get isAdmin(): boolean {
    return this.profile === 'Admin';
  }

  get isOfferManager(): boolean {
    return ['Teacher', 'Company'].includes(this.profile ?? '');
  }

  loginWithToken(ssoToken: string): Observable<void> {
    // Use HttpBackend directly to bypass all interceptors — ensures the SSO token
    // is used unmodified, not overridden by the auth interceptor's localStorage read.
    const http = new HttpClient(this.httpBackend);
    return http
      .get<{ user: { id: string; username: string; email: string; profile: string } }>(
        `${environment.apiBaseUrl}/auth/me`,
        { headers: new HttpHeaders({ Authorization: `Bearer ${ssoToken}` }) }
      )
      .pipe(
        tap(res => {
          const user = res.user;
          localStorage.setItem(this.TOKEN_KEY, ssoToken);
          localStorage.setItem(this.USER_KEY, JSON.stringify(user));
          this.currentUser = user;
          this.loggedIn = true;
        }),
        map(() => undefined as void)
      );
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem(this.TOKEN_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getUser(): { username: string; email: string; profile: string } | null {
    const raw = localStorage.getItem(this.USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      localStorage.removeItem(this.USER_KEY);
      return null;
    }
  }

  private storeSession(res: LoginResponse): void {
    localStorage.setItem(this.TOKEN_KEY, res.tokens.access_token);
    localStorage.setItem(this.REFRESH_KEY, res.tokens.refresh_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(res.user));
    this.currentUser = res.user;
    this.loggedIn = true;
  }

  private clearSession(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUser = null;
    this.loggedIn = false;
  }
}
