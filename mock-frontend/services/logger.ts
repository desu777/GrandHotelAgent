/**
 * Centralny logger dla mock-frontend
 * Poziomy: debug < info < warn < error
 * Kontrolowany przez VITE_LOG_LEVEL (domyślnie: debug)
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const currentLevel: LogLevel =
  (import.meta.env.VITE_LOG_LEVEL as LogLevel) || 'debug';

function log(
  level: LogLevel,
  component: string,
  msg: string,
  extra?: object
): void {
  if (LEVEL_PRIORITY[level] < LEVEL_PRIORITY[currentLevel]) return;

  const ts = new Date().toISOString();
  const prefix = `[${ts}] [${level.toUpperCase()}] [${component}]`;

  const method = level === 'debug' ? 'log' : level;
  if (extra) {
    console[method](prefix, msg, extra);
  } else {
    console[method](prefix, msg);
  }
}

export const logger = {
  debug: (component: string, msg: string, extra?: object) =>
    log('debug', component, msg, extra),
  info: (component: string, msg: string, extra?: object) =>
    log('info', component, msg, extra),
  warn: (component: string, msg: string, extra?: object) =>
    log('warn', component, msg, extra),
  error: (component: string, msg: string, extra?: object) =>
    log('error', component, msg, extra),
};
