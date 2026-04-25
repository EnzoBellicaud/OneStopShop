import { Component, Input } from '@angular/core';

const STATUS_MAP: Record<string, string> = {
  success: 'chip--success',
  partial: 'chip--partial',
  failed: 'chip--failed',
  running: 'chip--running',
  pending: 'chip--pending',
};

const METHOD_MAP: Record<string, string> = {
  llm_primary: 'chip--llm-primary',
  llm_fallback: 'chip--llm-fallback',
  deterministic: 'chip--deterministic',
};

@Component({
  selector: 'app-status-chip',
  standalone: true,
  template: `<span class="chip" [class]="chipClass">{{ label }}</span>`,
  styles: [`
    .chip {
      display: inline-block;
      padding: 0.1rem 0.5rem;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }
    .chip--success    { background: #e7f4ea; color: #1d7347; }
    .chip--partial    { background: #fff3cd; color: #856404; }
    .chip--failed     { background: #ffe4e4; color: #9e2a2a; }
    .chip--running    { background: #d0eaff; color: #1a5a8a; animation: pulse 1.5s ease-in-out infinite; }
    .chip--pending    { background: #e9ecef; color: #495057; }
    .chip--llm-primary   { background: #f0e6ff; color: #6f2da8; }
    .chip--llm-fallback  { background: #e8e6ff; color: #3730a3; }
    .chip--deterministic { background: #e9ecef; color: #495057; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.55} }
  `],
})
export class StatusChipComponent {
  @Input() status = '';
  @Input() variant: 'status' | 'method' = 'status';

  get chipClass(): string {
    const map = this.variant === 'method' ? METHOD_MAP : STATUS_MAP;
    return map[this.status] ?? 'chip--pending';
  }

  get label(): string {
    return this.status.replace(/_/g, ' ');
  }
}
