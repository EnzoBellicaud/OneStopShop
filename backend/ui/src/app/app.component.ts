import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './shared/auth.service';
import { OssApiService } from './shared/oss-api.service';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements OnInit {
  title = 'SUNRISE OSS';
  pendingCount = 0;
  readonly vueUrl: string = environment.vueBaseUrl;

  showChangePw = false;
  changePwForm = { old_password: '', new_password: '', confirm: '' };
  changePwError = signal<string | null>(null);
  changePwSuccess = signal(false);
  submittingPw = signal(false);

  constructor(
    readonly auth: AuthService,
    private readonly api: OssApiService,
    private readonly router: Router,
  ) {
    // SSO token always takes precedence — replace any existing session so authGuard passes
    const params = new URLSearchParams(window.location.search);
    const ssoToken = params.get('sso_token');
    if (ssoToken) {
      localStorage.setItem('oss.access_token', ssoToken);
      localStorage.removeItem('oss.user');
      auth.loggedIn = true;
      auth.currentUser = null;
    }
  }

  get publicSiteUrl(): string {
    const token = this.auth.getToken();
    return token ? `${this.vueUrl}?sso_token=${encodeURIComponent(token)}` : this.vueUrl;
  }

  ngOnInit(): void {
    const params = new URLSearchParams(window.location.search);
    const ssoToken = params.get('sso_token');

    if (ssoToken) {
      this.auth.loginWithToken(ssoToken).subscribe({
        next: () => {
          this.router.navigate(['/dashboard'], { replaceUrl: true });
          if (this.auth.isAdmin) {
            this._fetchPendingCount();
          }
        },
        error: () => {
          localStorage.removeItem('oss.access_token');
          this.auth.loggedIn = false;
          this.router.navigate(['/login'], { replaceUrl: true });
        },
      });
    } else if (this.auth.isAdmin) {
      this._fetchPendingCount();
    }
  }

  private _fetchPendingCount(): void {
    this.api.getUsers({ approval_status: 'pending', page_size: 1 }).subscribe({
      next: r => { this.pendingCount = r.count; },
      error: () => {},
    });
  }

  logout(): void {
    this.auth.logout();
  }

  submitChangePassword(): void {
    if (this.changePwForm.new_password !== this.changePwForm.confirm) {
      this.changePwError.set('New passwords do not match.');
      return;
    }
    if (this.changePwForm.new_password.length < 8) {
      this.changePwError.set('New password must be at least 8 characters.');
      return;
    }
    this.changePwError.set(null);
    this.submittingPw.set(true);
    this.api.changePassword(this.changePwForm.old_password, this.changePwForm.new_password).subscribe({
      next: () => {
        this.submittingPw.set(false);
        this.changePwSuccess.set(true);
      },
      error: (err) => {
        this.submittingPw.set(false);
        this.changePwError.set(err?.error?.detail ?? 'Failed to change password.');
      },
    });
  }

  closeChangePw(): void {
    this.showChangePw = false;
    this.changePwSuccess.set(false);
    this.changePwError.set(null);
    this.changePwForm = { old_password: '', new_password: '', confirm: '' };
  }
}
