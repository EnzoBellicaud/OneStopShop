import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface BarChartPoint {
  value: number;
  label: string;
}

interface Bar {
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  value: number;
}

@Component({
  selector: 'app-mini-bar-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chart-outer">
      <div class="chart-title" *ngIf="title">{{ title }}</div>
      <div class="chart-body" *ngIf="data.length; else empty">
        <svg [attr.width]="width" [attr.height]="svgHeight" [attr.viewBox]="'0 0 ' + width + ' ' + svgHeight" style="overflow:visible">
          <!-- Y-axis max label -->
          <text [attr.x]="plotLeft - 4" [attr.y]="plotTop" class="y-label" text-anchor="end" dominant-baseline="hanging">{{ maxVal }}</text>
          <text [attr.x]="plotLeft - 4" [attr.y]="plotBottom" class="y-label" text-anchor="end" dominant-baseline="auto">0</text>

          <!-- Y-axis line -->
          <line [attr.x1]="plotLeft" [attr.y1]="plotTop - 2" [attr.x2]="plotLeft" [attr.y2]="plotBottom" class="axis-line"/>
          <!-- X-axis line -->
          <line [attr.x1]="plotLeft" [attr.y1]="plotBottom" [attr.x2]="width" [attr.y2]="plotBottom" class="axis-line"/>

          <!-- Bars -->
          <g *ngFor="let bar of bars">
            <rect
              [attr.x]="bar.x"
              [attr.y]="bar.y"
              [attr.width]="bar.w"
              [attr.height]="bar.h"
              [attr.fill]="color"
              rx="2"
              class="bar">
              <title>{{ bar.label }}: {{ bar.value }}</title>
            </rect>
          </g>

          <!-- X-axis labels: first, mid, last -->
          <text *ngFor="let xl of xLabels"
            [attr.x]="xl.x"
            [attr.y]="svgHeight"
            [attr.text-anchor]="xl.anchor"
            class="x-label"
            dominant-baseline="auto">{{ xl.text }}</text>
        </svg>
        <div class="chart-summary">{{ total }} total · peak {{ maxVal }}</div>
      </div>
      <ng-template #empty>
        <div class="chart-empty">No data</div>
      </ng-template>
    </div>
  `,
  styles: [`
    .chart-outer { display: flex; flex-direction: column; gap: 0.3rem; }
    .chart-title {
      font-size: 0.72rem;
      color: #5a6e7f;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .chart-body { display: flex; flex-direction: column; gap: 0.2rem; }
    .chart-summary { font-size: 0.72rem; color: #6a7e8f; }
    .chart-empty { font-size: 0.78rem; color: #9aaabb; padding: 1rem 0; }
    .axis-line { stroke: #d0dbe8; stroke-width: 1; }
    .bar { opacity: 0.82; transition: opacity 0.1s; }
    .bar:hover { opacity: 1; }
    .y-label { font-size: 9px; fill: #7a8ea0; font-family: inherit; }
    .x-label { font-size: 9px; fill: #7a8ea0; font-family: inherit; }
  `],
})
export class MiniBarChartComponent implements OnChanges {
  @Input() data: BarChartPoint[] = [];
  @Input() color = '#23638f';
  @Input() title = '';
  @Input() width = 280;
  @Input() barHeight = 80;

  readonly plotLeft = 26;
  readonly plotTop = 6;
  readonly xAxisPad = 14;

  bars: Bar[] = [];
  xLabels: { x: number; text: string; anchor: string }[] = [];
  maxVal = 0;
  total = 0;

  get plotBottom(): number { return this.barHeight; }
  get plotWidth(): number { return this.width - this.plotLeft; }
  get plotHeight(): number { return this.plotBottom - this.plotTop; }
  get svgHeight(): number { return this.barHeight + this.xAxisPad; }

  ngOnChanges(): void {
    this.compute();
  }

  private compute(): void {
    const n = this.data.length;
    if (!n) { this.bars = []; this.xLabels = []; this.maxVal = 0; this.total = 0; return; }

    this.maxVal = Math.max(...this.data.map((d) => d.value), 1);
    this.total = this.data.reduce((s, d) => s + d.value, 0);

    const slotW = this.plotWidth / n;
    const gap = Math.max(1, slotW * 0.18);

    this.bars = this.data.map((d, i) => {
      const h = d.value > 0
        ? Math.max(2, (d.value / this.maxVal) * this.plotHeight)
        : 0;
      return {
        x: this.plotLeft + i * slotW + gap / 2,
        y: this.plotBottom - h,
        w: slotW - gap,
        h,
        label: d.label,
        value: d.value,
      };
    });

    this.xLabels = [];
    const addLabel = (i: number, anchor: string) => {
      const x = this.plotLeft + (i + 0.5) * slotW;
      this.xLabels.push({ x, text: this.data[i].label, anchor });
    };
    addLabel(0, 'start');
    if (n > 2) addLabel(Math.floor(n / 2), 'middle');
    if (n > 1) addLabel(n - 1, 'end');
  }
}
