import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sparkline',
  standalone: true,
  template: `
    <svg [attr.width]="width" [attr.height]="height" [attr.viewBox]="'0 0 ' + width + ' ' + height" style="overflow:visible">
      <polyline
        *ngIf="points"
        [attr.points]="points"
        fill="none"
        [attr.stroke]="color"
        stroke-width="1.5"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
    </svg>
  `,
  styles: [`:host { display: inline-block; vertical-align: middle; }`],
  imports: [CommonModule],
})
export class SparklineComponent implements OnChanges {
  @Input() values: number[] = [];
  @Input() width = 120;
  @Input() height = 28;
  @Input() color = '#23638f';

  points = '';

  ngOnChanges(): void {
    this.points = this.buildPoints();
  }

  private buildPoints(): string {
    const { values, width, height } = this;
    if (!values.length) return '';
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const pad = 2;
    const w = width - pad * 2;
    const h = height - pad * 2;
    return values
      .map((v, i) => {
        const x = pad + (i / Math.max(values.length - 1, 1)) * w;
        const y = pad + h - ((v - min) / range) * h;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }
}
