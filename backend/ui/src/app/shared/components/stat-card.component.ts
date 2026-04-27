import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stat-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="stat-card" [attr.data-tone]="tone">
      <span class="label">{{ label }}</span>
      <strong class="value">{{ value }}</strong>
      <span class="delta" *ngIf="delta !== undefined">{{ delta > 0 ? '+' : '' }}{{ delta }}</span>
      <span class="hint" *ngIf="hint">{{ hint }}</span>
    </div>
  `,
  styles: [`
    .stat-card {
      border: 1px solid #dde7f1;
      border-radius: 12px;
      padding: 0.75rem 1rem;
      display: grid;
      gap: 0.15rem;
      background: #fff;
    }
    .stat-card[data-tone="positive"] { border-color: #b3dfc0; background: #f3fbf5; }
    .stat-card[data-tone="warning"] { border-color: #f0d08b; background: #fffdf0; }
    .stat-card[data-tone="danger"] { border-color: #f0b3b3; background: #fff5f5; }
    .label { font-size: 0.72rem; color: #5a6e7f; text-transform: uppercase; letter-spacing: 0.06em; }
    .value { font-size: 1.6rem; color: #1f3041; font-weight: 700; line-height: 1.1; }
    .delta { font-size: 0.78rem; color: #5a7a5a; }
    .hint { font-size: 0.7rem; color: #8a9aaa; }
  `],
})
export class StatCardComponent {
  @Input() label = '';
  @Input() value: string | number = '';
  @Input() delta?: number;
  @Input() hint?: string;
  @Input() tone: 'neutral' | 'positive' | 'warning' | 'danger' = 'neutral';
}
