import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { MockOpportunity, MockOpportunityCreateRequest } from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';
import { TranslatePipe } from '../shared/i18n/translate.pipe';

@Component({
  selector: 'app-mock-site-admin-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './mock-site-admin-page.component.html',
  styleUrl: './mock-site-admin-page.component.css',
})
export class MockSiteAdminPageComponent implements OnInit, OnDestroy {
  mockOpportunities: MockOpportunity[] = [];
  loadingMock = false;
  showMockModal = false;
  savingMock = false;
  deletingMock: string | null = null;
  mockForm: MockOpportunityCreateRequest = {
    title: '',
    description: '',
    offer_type: 'internship',
    target_profile: 'student',
  };
  mockError: string | null = null;

  private readonly destroy$ = new Subject<void>();

  constructor(private readonly api: OssApiService) {}

  ngOnInit(): void {
    this.loadMockOpportunities();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMockOpportunities(): void {
    this.loadingMock = true;
    this.api.getMockOpportunities().pipe(takeUntil(this.destroy$)).subscribe({
      next: (res) => {
        this.mockOpportunities = res.results;
        this.loadingMock = false;
      },
      error: () => { this.loadingMock = false; },
    });
  }

  openAddOpportunity(): void {
    this.mockForm = { title: '', description: '', offer_type: 'internship', target_profile: 'student' };
    this.mockError = null;
    this.showMockModal = true;
  }

  closeMockModal(): void {
    this.showMockModal = false;
  }

  saveOpportunity(): void {
    if (!this.mockForm.title.trim()) {
      this.mockError = 'Title is required.';
      return;
    }
    this.mockError = null;
    this.savingMock = true;
    this.api.createMockOpportunity(this.mockForm).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.savingMock = false;
        this.showMockModal = false;
        this.loadMockOpportunities();
      },
      error: () => {
        this.savingMock = false;
        this.mockError = 'Failed to create opportunity.';
      },
    });
  }

  deleteOpportunity(id: string): void {
    if (!confirm('Delete this opportunity from the mock site?')) return;
    this.deletingMock = id;
    this.api.deleteMockOpportunity(id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.deletingMock = null;
        this.mockOpportunities = this.mockOpportunities.filter(o => o.id !== id);
      },
      error: () => { this.deletingMock = null; },
    });
  }
}
