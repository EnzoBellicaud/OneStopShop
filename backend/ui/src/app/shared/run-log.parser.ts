export type RunLogEntry = {
  ts?: string;
  level?: 'info' | 'warn' | 'error';
  event?: string;
  url?: string;
  source_key?: string;
  method?: string;
  confidence?: number;
  model?: string;
  http_status?: number;
  duration_ms?: number;
  message?: string;
  reason?: string;
  action?: string;
  seconds?: number;
  raw: Record<string, unknown>;
};

export type UrlResult = {
  url: string;
  method?: string;
  http_status?: number;
  confidence?: number;
  duration_ms?: number;
  failed: boolean;
  neglected: boolean;
  message?: string;
  reason?: string;
  action?: string;
  ts?: string;
};

export function parseRunLog(log: unknown[]): RunLogEntry[] {
  if (!Array.isArray(log)) return [];
  return log.map((raw) => {
    if (!raw || typeof raw !== 'object') {
      return { raw: { value: raw } as Record<string, unknown> };
    }
    const e = raw as Record<string, unknown>;
    return {
      ts: typeof e['ts'] === 'string' ? e['ts'] : undefined,
      level: ['info', 'warn', 'error'].includes(e['level'] as string)
        ? (e['level'] as 'info' | 'warn' | 'error')
        : undefined,
      event: typeof e['event'] === 'string' ? e['event'] : undefined,
      url: typeof e['url'] === 'string' ? e['url'] : undefined,
      source_key: typeof e['source_key'] === 'string' ? e['source_key'] : undefined,
      method: typeof e['method'] === 'string' ? e['method'] : undefined,
      confidence: typeof e['confidence'] === 'number' ? e['confidence'] : undefined,
      model: typeof e['model'] === 'string' ? e['model'] : undefined,
      http_status: typeof e['http_status'] === 'number' ? e['http_status'] : undefined,
      duration_ms: typeof e['duration_ms'] === 'number' ? e['duration_ms'] : undefined,
      message: typeof e['message'] === 'string' ? e['message'] : undefined,
      reason: typeof e['reason'] === 'string' ? e['reason'] : undefined,
      action: typeof e['action'] === 'string' ? e['action'] : undefined,
      seconds: typeof e['seconds'] === 'number' ? e['seconds'] : undefined,
      raw: e,
    };
  });
}

export function groupByEvent(entries: RunLogEntry[]): Record<string, RunLogEntry[]> {
  const result: Record<string, RunLogEntry[]> = {};
  for (const entry of entries) {
    const key = entry.event ?? '__unknown__';
    (result[key] ??= []).push(entry);
  }
  return result;
}

export function toUrlResults(entries: RunLogEntry[]): UrlResult[] {
  const urlMap = new Map<string, UrlResult>();
  for (const entry of entries) {
    if (!entry.url) continue;
    const existing = urlMap.get(entry.url);
    // Old runs logged neglected URLs as event=url_failed level=info.
    // New runs use event=url_neglected. Use level to distinguish.
    const isNeglect =
      entry.event === 'url_neglected' ||
      (entry.event === 'url_failed' && entry.level === 'info');

    if (!existing) {
      urlMap.set(entry.url, {
        url: entry.url,
        method: entry.method,
        http_status: entry.http_status,
        confidence: entry.confidence,
        duration_ms: entry.duration_ms,
        failed: entry.event === 'url_failed' && !isNeglect,
        neglected: isNeglect,
        message: entry.message,
        reason: entry.reason,
        action: entry.action,
        ts: entry.ts,
      });
    } else if (entry.event === 'url_processed') {
      urlMap.set(entry.url, {
        ...existing,
        method: entry.method ?? existing.method,
        confidence: entry.confidence ?? existing.confidence,
        duration_ms: entry.duration_ms ?? existing.duration_ms,
        failed: false,
        neglected: false,
        action: entry.action ?? existing.action,
        ts: entry.ts ?? existing.ts,
      });
    } else if (isNeglect) {
      urlMap.set(entry.url, {
        ...existing,
        neglected: true,
        failed: false,
        reason: entry.reason ?? existing.reason,
        ts: entry.ts ?? existing.ts,
      });
    } else if (entry.event === 'url_failed') {
      urlMap.set(entry.url, {
        ...existing,
        failed: true,
        neglected: false,
        http_status: entry.http_status ?? existing.http_status,
        message: entry.message ?? existing.message,
        reason: entry.reason ?? existing.reason,
        ts: entry.ts ?? existing.ts,
      });
    }
  }
  return Array.from(urlMap.values());
}
