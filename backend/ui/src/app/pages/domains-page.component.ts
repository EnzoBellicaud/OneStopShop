import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AllowedDomainCreateRequest, AllowedDomainItem, OrganizationLookup } from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';

@Component({
  selector: 'app-domains-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './domains-page.component.html',
  styleUrls: ['./domains-page.component.css'],
})
export class DomainsPageComponent implements OnInit {
  private readonly api = inject(OssApiService);

  domains: AllowedDomainItem[] = [];
  organizations: OrganizationLookup[] = [];
  loading = signal(false);
  error = signal<string | null>(null);

  showForm = false;
  editTarget: AllowedDomainItem | null = null;
  form: AllowedDomainCreateRequest = { domain: '', organization_id: '', description: '' };
  saving = signal(false);
  formError = signal<string | null>(null);

  confirmDeleteId: string | null = null;

  ngOnInit(): void {
    this.load();
    this.api.getOrganizations().subscribe({ next: r => { this.organizations = r.results; } });
  }

  load(): void {
    this.loading.set(true);
    this.api.getAllowedDomains().subscribe({
      next: r => { this.domains = r.results; this.loading.set(false); },
      error: () => { this.error.set('Failed to load domains.'); this.loading.set(false); },
    });
  }

  openAdd(): void {
    this.editTarget = null;
    this.form = { domain: '', organization_id: '', description: '' };
    this.formError.set(null);
    this.showForm = true;
  }

  openEdit(d: AllowedDomainItem): void {
    this.editTarget = d;
    this.form = { domain: d.domain, organization_id: d.organization_id, description: d.description };
    this.formError.set(null);
    this.showForm = true;
  }

  save(): void {
    this.formError.set(null);
    this.saving.set(true);
    const obs = this.editTarget
      ? this.api.updateAllowedDomain(this.editTarget.id, this.form)
      : this.api.createAllowedDomain(this.form);

    obs.subscribe({
      next: () => { this.saving.set(false); this.showForm = false; this.load(); },
      error: (err) => {
        this.saving.set(false);
        const msg = err?.error?.message ?? err?.error?.domain?.[0] ?? 'Save failed.';
        this.formError.set(msg);
      },
    });
  }

  confirmDelete(id: string): void {
    this.confirmDeleteId = id;
  }

  doDelete(): void {
    if (!this.confirmDeleteId) return;
    this.api.deleteAllowedDomain(this.confirmDeleteId).subscribe({
      next: () => { this.confirmDeleteId = null; this.load(); },
      error: () => this.error.set('Delete failed.'),
    });
  }

  orgName(orgId: string): string {
    return this.organizations.find(o => o.id === orgId)?.name ?? orgId;
  }
}
