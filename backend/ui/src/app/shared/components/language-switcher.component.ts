import { Component, ElementRef, HostListener, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslationService } from '../i18n/translation.service';

@Component({
  selector: 'app-language-switcher',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="lang-picker">
      <button
        type="button"
        class="lang-btn"
        [attr.aria-expanded]="open()"
        aria-haspopup="menu"
        (click)="open.set(!open())"
      >
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="8" cy="8" r="6.5" />
          <path d="M8 1.5C8 1.5 6 4.5 6 8s2 6.5 2 6.5M8 1.5C8 1.5 10 4.5 10 8s-2 6.5-2 6.5M1.5 8h13" />
          <path d="M2 5h12M2 11h12" />
        </svg>
        <span>{{ i18n.locale().toUpperCase() }}</span>
        <svg class="chevron" [class.open]="open()" viewBox="0 0 10 6" fill="none"
             stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
          <path d="M1 1l4 4 4-4" />
        </svg>
      </button>

      @if (open()) {
        <ul class="lang-dropdown" role="menu">
          @for (lang of i18n.locales; track lang.code) {
            <li role="none">
              <button
                role="menuitemradio"
                [attr.aria-checked]="lang.code === i18n.locale()"
                class="lang-option"
                [class.active]="lang.code === i18n.locale()"
                (click)="select(lang.code)"
              >
                {{ lang.label }}
                @if (lang.code === i18n.locale()) {
                  <svg viewBox="0 0 12 10" fill="none" stroke="currentColor" stroke-width="2"
                       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M1 5l3.5 3.5L11 1" />
                  </svg>
                }
              </button>
            </li>
          }
        </ul>
      }
    </div>
  `,
  styles: [`
    .lang-picker { position: relative; }
    .lang-btn {
      display: flex; align-items: center; gap: 5px;
      padding: 5px 10px; border: 1px solid rgba(128,128,128,0.45);
      border-radius: 6px; background: transparent; color: inherit;
      font-size: 12px; font-weight: 500; cursor: pointer;
      transition: border-color .15s, color .15s; white-space: nowrap;
    }
    .lang-btn:hover { border-color: currentColor; }
    .lang-btn svg:first-of-type { width: 14px; height: 14px; flex-shrink: 0; }
    .chevron { width: 8px; height: 6px; flex-shrink: 0; transition: transform .2s; }
    .chevron.open { transform: rotate(180deg); }
    .lang-dropdown {
      position: absolute; top: calc(100% + 6px); left: 0; min-width: 140px;
      margin: 0; padding: 0; list-style: none; background: #fff; color: #111110;
      border: 1px solid #e4e4e0; border-radius: 6px;
      box-shadow: 0 4px 16px rgba(0,0,0,.18); z-index: 200; overflow: hidden;
    }
    .lang-option {
      display: flex; align-items: center; justify-content: space-between;
      width: 100%; padding: 9px 14px; background: none; border: none;
      font-size: 13px; color: #111110; cursor: pointer; text-align: left;
      transition: background .12s; gap: 8px;
    }
    .lang-option:hover { background: #fafaf8; }
    .lang-option.active { font-weight: 600; }
    .lang-option svg { width: 12px; height: 10px; flex-shrink: 0; color: #9b2020; }
  `],
})
export class LanguageSwitcherComponent {
  readonly open = signal(false);

  constructor(public readonly i18n: TranslationService, private readonly host: ElementRef) {}

  select(code: string): void {
    this.i18n.setLocale(code);
    this.open.set(false);
  }

  @HostListener('document:mousedown', ['$event'])
  onClickOutside(e: MouseEvent): void {
    if (!this.host.nativeElement.contains(e.target)) this.open.set(false);
  }

  @HostListener('document:keydown.escape')
  onEsc(): void {
    this.open.set(false);
  }
}
