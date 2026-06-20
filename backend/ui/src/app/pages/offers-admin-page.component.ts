import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import {
  OfferTypeAdmin,
  OfferTypeAdminCreateRequest,
  OfferTypeAdminListResponse,
} from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';
import { TranslatePipe } from '../shared/i18n/translate.pipe';

@Component({
  selector: 'app-offers-admin-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './offers-admin-page.component.html',
  styleUrl: './offers-admin-page.component.css',
})
export class OffersAdminPageComponent implements OnInit, OnDestroy {
  offerTypes: OfferTypeAdmin[] = [];
  loadingOfferTypes = false;
  offerTypeForm: OfferTypeAdminCreateRequest = { name: '', description: '', keywords: '' };
  editingOfferTypeId: string | null = null;
  showOfferTypeModal = false;
  offerTypeError: string | null = null;

  private readonly destroy$ = new Subject<void>();

  constructor(private readonly api: OssApiService) {}

  ngOnInit(): void {
    this.loadOfferTypes();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadOfferTypes(): void {
    this.loadingOfferTypes = true;
    this.api.getAdminOfferTypes().pipe(takeUntil(this.destroy$)).subscribe({
      next: (res: OfferTypeAdminListResponse) => {
        this.offerTypes = res.results;
        this.loadingOfferTypes = false;
      },
      error: () => { this.loadingOfferTypes = false; },
    });
  }

  openNewOfferType(): void {
    this.editingOfferTypeId = null;
    this.offerTypeForm = { name: '', description: '', keywords: '' };
    this.offerTypeError = null;
    this.showOfferTypeModal = true;
  }

  openEditOfferType(ot: OfferTypeAdmin): void {
    this.editingOfferTypeId = ot.id;
    this.offerTypeForm = { name: ot.name, description: ot.description, keywords: ot.keywords };
    this.offerTypeError = null;
    this.showOfferTypeModal = true;
  }

  saveOfferType(): void {
    this.offerTypeError = null;
    const obs = this.editingOfferTypeId
      ? this.api.patchAdminOfferType(this.editingOfferTypeId, this.offerTypeForm)
      : this.api.createAdminOfferType(this.offerTypeForm);
    obs.pipe(takeUntil(this.destroy$)).subscribe({
      next: (saved: OfferTypeAdmin) => {
        if (this.editingOfferTypeId) {
          this.offerTypes = this.offerTypes.map(ot => ot.id === saved.id ? saved : ot);
        } else {
          this.offerTypes = [...this.offerTypes, saved];
        }
        this.showOfferTypeModal = false;
      },
      error: () => { this.offerTypeError = 'Failed to save offer type. Check all required fields.'; },
    });
  }

  deleteOfferType(id: string): void {
    if (!confirm('Delete this offer type?')) return;
    this.api.deleteAdminOfferType(id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => { this.offerTypes = this.offerTypes.filter(ot => ot.id !== id); },
      error: () => { this.offerTypeError = 'Failed to delete offer type. It may be in use by existing offers.'; },
    });
  }

  keywordCount(ot: OfferTypeAdmin): string {
    if (!ot.keywords) return '—';
    return ot.keywords.split(',').filter(k => k.trim()).length + ' keywords';
  }
}
