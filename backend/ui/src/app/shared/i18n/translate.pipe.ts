import { Pipe, PipeTransform } from '@angular/core';
import { TranslationService } from './translation.service';

/**
 * Usage in templates:
 *   {{ 'dashboard.title' | translate }}
 *   {{ 'users.count' | translate:{ n: total } }}
 *
 * Impure so it re-evaluates when the active locale changes. Reading the locale
 * signal inside transform also ties it into change detection.
 */
@Pipe({ name: 'translate', standalone: true, pure: false })
export class TranslatePipe implements PipeTransform {
  constructor(private readonly i18n: TranslationService) {}

  transform(key: string, params?: Record<string, string | number>): string {
    // Touch the signal so the pipe stays reactive to locale changes.
    this.i18n.locale();
    return this.i18n.translate(key, params);
  }
}
