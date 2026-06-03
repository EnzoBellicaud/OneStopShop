import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  AdminCreateOrgRequest,
  AdminCreateUserRequest,
  AdminUsersListQueryParams,
  OrganizationLookup,
  UserApprovalRequest,
  UserManagementSummary,
} from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';

@Component({
  selector: 'app-users-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './users-page.component.html',
  styleUrls: ['./users-page.component.css'],
})
export class UsersPageComponent implements OnInit {
  private readonly api = inject(OssApiService);

  users: UserManagementSummary[] = [];
  total = 0;
  loading = signal(false);
  error = signal<string | null>(null);

  // Filters
  filters: AdminUsersListQueryParams = { page: 1, page_size: 20 };
  searchInput = '';

  // Reject modal
  rejectTarget: UserManagementSummary | null = null;
  rejectNotes = '';

  // Assign org modal
  assignOrgTarget: UserManagementSummary | null = null;
  assignOrgId = '';
  organizations: OrganizationLookup[] = [];
  showNewOrgForm = false;
  newOrgForm: AdminCreateOrgRequest = { name: '', type: 'company', country: '', website: '' };
  creatingOrg = signal(false);

  // Create user modal
  showCreateModal = false;
  createForm: AdminCreateUserRequest = { username: '', email: '', password: '', profile: 'Student' };
  createError = signal<string | null>(null);
  createSuccess = signal<string | null>(null);
  creatingUser = signal(false);

  readonly profiles = ['Student', 'Academic staff', 'Teacher', 'Company', 'Admin'];

  ngOnInit(): void {
    this.load();
    this.api.getOrganizations().subscribe({ next: r => { this.organizations = r.results; }, error: () => {} });
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.getUsers(this.filters).subscribe({
      next: r => {
        this.users = r.results;
        this.total = r.count;
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load users.');
        this.loading.set(false);
      },
    });
  }

  applySearch(): void {
    this.filters = { ...this.filters, search: this.searchInput || undefined, page: 1 };
    this.load();
  }

  setFilter(key: keyof AdminUsersListQueryParams, value: string): void {
    this.filters = { ...this.filters, [key]: value || undefined, page: 1 };
    this.load();
  }

  approve(user: UserManagementSummary): void {
    const payload: UserApprovalRequest = { action: 'approve', email_verified: true };
    this.api.approveUser(user.id, payload).subscribe({
      next: updated => this.replaceUser(updated),
      error: () => this.error.set('Approve failed.'),
    });
  }

  openReject(user: UserManagementSummary): void {
    this.rejectTarget = user;
    this.rejectNotes = '';
  }

  confirmReject(): void {
    if (!this.rejectTarget) return;
    const payload: UserApprovalRequest = { action: 'reject', notes: this.rejectNotes };
    this.api.approveUser(this.rejectTarget.id, payload).subscribe({
      next: updated => { this.replaceUser(updated); this.rejectTarget = null; },
      error: () => this.error.set('Reject failed.'),
    });
  }

  toggleEmailVerified(user: UserManagementSummary): void {
    const payload: UserApprovalRequest = { email_verified: !user.email_verified };
    this.api.approveUser(user.id, payload).subscribe({
      next: updated => this.replaceUser(updated),
      error: () => this.error.set('Update failed.'),
    });
  }

  changeRole(user: UserManagementSummary, profile: string): void {
    this.api.changeUserRole(user.id, profile).subscribe({
      next: updated => this.replaceUser(updated),
      error: () => this.error.set('Role change failed.'),
    });
  }

  openAssignOrg(user: UserManagementSummary): void {
    this.assignOrgTarget = user;
    this.assignOrgId = user.organization_id ?? '';
    this.showNewOrgForm = false;
    this.newOrgForm = { name: '', type: 'company', country: '', website: '' };
  }

  createAndSelectOrg(): void {
    if (!this.newOrgForm.name || !this.newOrgForm.country) return;
    this.creatingOrg.set(true);
    this.api.createOrganization(this.newOrgForm).subscribe({
      next: org => {
        this.organizations = [...this.organizations, org];
        this.assignOrgId = org.id;
        this.showNewOrgForm = false;
        this.creatingOrg.set(false);
      },
      error: () => {
        this.error.set('Failed to create organization.');
        this.creatingOrg.set(false);
      },
    });
  }

  confirmAssignOrg(): void {
    if (!this.assignOrgTarget || !this.assignOrgId) return;
    this.api.linkUserOrganization(this.assignOrgTarget.id, this.assignOrgId).subscribe({
      next: () => {
        this.assignOrgTarget = null;
        this.load();
      },
      error: () => this.error.set('Failed to assign organization.'),
    });
  }

  toggleActive(user: UserManagementSummary): void {
    this.api.updateUser(user.id, { is_active: !user.is_active }).subscribe({
      next: updated => this.replaceUser(updated),
      error: () => this.error.set('Update failed.'),
    });
  }

  openCreateModal(): void {
    this.createForm = { username: '', email: '', password: '', profile: 'Student' };
    this.createError.set(null);
    this.createSuccess.set(null);
    this.showCreateModal = true;
  }

  submitCreate(): void {
    this.createError.set(null);
    this.creatingUser.set(true);
    this.api.createAdminUser(this.createForm).subscribe({
      next: user => {
        this.creatingUser.set(false);
        this.createSuccess.set(`User "${user.username}" created.`);
        this.load();
      },
      error: () => {
        this.creatingUser.set(false);
        this.createError.set('Failed to create user.');
      },
    });
  }

  prevPage(): void {
    if ((this.filters.page ?? 1) > 1) {
      this.filters = { ...this.filters, page: (this.filters.page ?? 1) - 1 };
      this.load();
    }
  }

  nextPage(): void {
    const pageSize = this.filters.page_size ?? 20;
    if ((this.filters.page ?? 1) * pageSize < this.total) {
      this.filters = { ...this.filters, page: (this.filters.page ?? 1) + 1 };
      this.load();
    }
  }

  private replaceUser(updated: UserManagementSummary): void {
    this.users = this.users.map(u => u.id === updated.id ? updated : u);
  }
}
