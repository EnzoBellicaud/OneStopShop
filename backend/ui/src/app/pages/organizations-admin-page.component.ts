import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { AdminCreateOrgRequest, OrganizationDetail } from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';
import { TranslatePipe } from '../shared/i18n/translate.pipe';

@Component({
  selector: 'app-organizations-admin-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './organizations-admin-page.component.html',
  styleUrl: './organizations-admin-page.component.css',
})
export class OrganizationsAdminPageComponent implements OnInit, OnDestroy {
  organizations: OrganizationDetail[] = [];
  loading = false;
  showModal = false;
  saving = false;
  deletingId: string | null = null;
  editingOrg: OrganizationDetail | null = null;
  error: string | null = null;

  form: AdminCreateOrgRequest = {
    name: '',
    type: 'university',
    country: '',
    website: '',
  };

  private readonly destroy$ = new Subject<void>();

  constructor(private readonly api: OssApiService) {}

  ngOnInit(): void {
    this.loadOrganizations();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadOrganizations(): void {
    this.loading = true;
    this.error = null;
    this.api.getAdminOrganizations()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => { this.organizations = res.results; this.loading = false; },
        error: () => { this.error = 'Failed to load organizations.'; this.loading = false; },
      });
  }

  openAdd(): void {
    this.editingOrg = null;
    this.form = { name: '', type: 'university', country: '', website: '' };
    this.error = null;
    this.showModal = true;
  }

  openEdit(org: OrganizationDetail): void {
    this.editingOrg = org;
    this.form = { name: org.name, type: org.type as AdminCreateOrgRequest['type'], country: org.country, website: org.website };
    this.error = null;
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
    this.editingOrg = null;
    this.error = null;
  }

  submit(): void {
    if (!this.form.name.trim()) { this.error = 'Name is required.'; return; }
    if (!this.form.country || this.form.country.length !== 2) { this.error = 'Country must be a 2-letter ISO code.'; return; }
    this.saving = true;
    this.error = null;

    if (this.editingOrg) {
      this.api.updateOrganization(this.editingOrg.id, this.form)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (updated) => {
            this.organizations = this.organizations.map(o => o.id === updated.id ? updated : o)
              .sort((a, b) => a.name.localeCompare(b.name));
            this.saving = false;
            this.showModal = false;
            this.editingOrg = null;
          },
          error: (err) => {
            this.error = err?.error?.message ?? 'Failed to update organization.';
            this.saving = false;
          },
        });
    } else {
      this.api.createOrganization(this.form)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (org) => {
            this.organizations = [...this.organizations, org].sort((a, b) => a.name.localeCompare(b.name));
            this.saving = false;
            this.showModal = false;
          },
          error: (err) => {
            this.error = err?.error?.message ?? 'Failed to create organization.';
            this.saving = false;
          },
        });
    }
  }

  deleteOrg(org: OrganizationDetail): void {
    if (!confirm(`Delete "${org.name}"? This cannot be undone.`)) return;
    this.deletingId = org.id;
    this.error = null;
    this.api.deleteOrganization(org.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.organizations = this.organizations.filter(o => o.id !== org.id);
          this.deletingId = null;
        },
        error: (err) => {
          this.deletingId = null;
          this.error = err?.error?.message ?? `Cannot delete "${org.name}". It may still have linked offers or sources.`;
        },
      });
  }
}
