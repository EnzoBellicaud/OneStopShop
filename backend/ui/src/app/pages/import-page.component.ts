import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ConfirmResult, ImportInvalidRow, ImportValidRow, PreviewResult } from '../shared/api.models';
import { OssApiService } from '../shared/oss-api.service';

type PageState = 'upload' | 'preview' | 'result';
type RowStatus = 'draft' | 'published';

@Component({
  selector: 'app-import-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './import-page.component.html',
  styleUrls: ['./import-page.component.css'],
})
export class ImportPageComponent {
  private readonly api = inject(OssApiService);

  state = signal<PageState>('upload');
  activeTab = signal<'new' | 'existing'>('new');

  // Upload state
  selectedFile: File | null = null;
  uploading = signal(false);
  uploadError = signal<string | null>(null);

  // Preview state
  validRows: ImportValidRow[] = [];
  invalidRows: ImportInvalidRow[] = [];
  selectedRows = new Set<number>();
  rowStatuses = new Map<number, RowStatus>();

  // Result state
  confirmResult: ConfirmResult | null = null;
  confirming = signal(false);
  confirmError = signal<string | null>(null);

  get newRows(): ImportValidRow[] {
    return this.validRows.filter(
      (r) => !r.warnings.some((w) => w.includes('URL already exists')),
    );
  }

  get existingRows(): ImportValidRow[] {
    return this.validRows.filter((r) =>
      r.warnings.some((w) => w.includes('URL already exists')),
    );
  }

  get activeRows(): ImportValidRow[] {
    return this.activeTab() === 'new' ? this.newRows : this.existingRows;
  }

  get allSelected(): boolean {
    const rows = this.activeRows;
    return rows.length > 0 && rows.every((r) => this.selectedRows.has(r.row));
  }

  get someSelected(): boolean {
    const rows = this.activeRows;
    return rows.some((r) => this.selectedRows.has(r.row)) && !this.allSelected;
  }

  get totalSelected(): number {
    return this.selectedRows.size;
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
    this.uploadError.set(null);
  }

  onPreview(): void {
    if (!this.selectedFile) return;
    this.uploading.set(true);
    this.uploadError.set(null);

    this.api.previewImport(this.selectedFile).subscribe({
      next: (result: PreviewResult) => {
        this.uploading.set(false);
        this.validRows = result.valid;
        this.invalidRows = result.invalid;
        this.selectedRows = new Set(result.valid.map((r) => r.row));
        this.rowStatuses = new Map(result.valid.map((r) => [r.row, 'draft']));
        this.activeTab.set('new');
        this.state.set('preview');
      },
      error: (err) => {
        this.uploading.set(false);
        this.uploadError.set(err?.error?.error ?? 'Failed to parse file. Check format and try again.');
      },
    });
  }

  toggleRow(row: number): void {
    if (this.selectedRows.has(row)) {
      this.selectedRows.delete(row);
    } else {
      this.selectedRows.add(row);
    }
    this.selectedRows = new Set(this.selectedRows);
  }

  toggleAll(): void {
    const rows = this.activeRows;
    if (this.allSelected) {
      rows.forEach((r) => this.selectedRows.delete(r.row));
    } else {
      rows.forEach((r) => this.selectedRows.add(r.row));
    }
    this.selectedRows = new Set(this.selectedRows);
  }

  isSelected(row: number): boolean {
    return this.selectedRows.has(row);
  }

  getRowStatus(row: number): RowStatus {
    return this.rowStatuses.get(row) ?? 'draft';
  }

  setRowStatus(row: number, event: Event): void {
    const value = (event.target as HTMLSelectElement).value as RowStatus;
    this.rowStatuses.set(row, value);
    this.rowStatuses = new Map(this.rowStatuses);
  }

  onConfirm(): void {
    const rows = this.validRows
      .filter((r) => this.selectedRows.has(r.row))
      .map((r) => ({ ...r, status: this.getRowStatus(r.row) }));

    if (rows.length === 0) return;

    this.confirming.set(true);
    this.confirmError.set(null);

    this.api.confirmImport(rows).subscribe({
      next: (result: ConfirmResult) => {
        this.confirming.set(false);
        this.confirmResult = result;
        this.state.set('result');
      },
      error: (err) => {
        this.confirming.set(false);
        this.confirmError.set(err?.error?.error ?? 'Import failed. Please try again.');
      },
    });
  }

  onDownloadTemplate(): void {
    this.api.getImportTemplate();
  }

  onBack(): void {
    this.state.set('upload');
    this.selectedFile = null;
    this.uploadError.set(null);
  }

  onReset(): void {
    this.state.set('upload');
    this.selectedFile = null;
    this.validRows = [];
    this.invalidRows = [];
    this.selectedRows = new Set();
    this.rowStatuses = new Map();
    this.confirmResult = null;
    this.uploadError.set(null);
    this.confirmError.set(null);
  }
}
