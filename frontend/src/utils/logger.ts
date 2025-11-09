/**
 * Logging utility to provide conditional logging in development vs production
 *
 * Usage:
 *   import { logger } from '@/utils/logger';
 *   logger.debug('Debug message', data);
 *   logger.info('Info message', data);
 *   logger.warn('Warning message', data);
 *   logger.error('Error message', error);
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  enabled: boolean;
  minLevel: LogLevel;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class Logger {
  private config: LoggerConfig;

  constructor() {
    // Enable logging in development, disable debug logs in production
    this.config = {
      enabled: import.meta.env.MODE !== 'production' || import.meta.env.VITE_ENABLE_LOGGING === 'true',
      minLevel: import.meta.env.MODE === 'production' ? 'warn' : 'debug',
    };
  }

  private shouldLog(level: LogLevel): boolean {
    return this.config.enabled && LOG_LEVELS[level] >= LOG_LEVELS[this.config.minLevel];
  }

  private formatMessage(level: LogLevel, message: string, data?: unknown): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    return data !== undefined ? `${prefix} ${message}` : `${prefix} ${message}`;
  }

  debug(message: string, data?: unknown): void {
    if (this.shouldLog('debug')) {
      if (data !== undefined) {
        console.log(this.formatMessage('debug', message), data);
      } else {
        console.log(this.formatMessage('debug', message));
      }
    }
  }

  info(message: string, data?: unknown): void {
    if (this.shouldLog('info')) {
      if (data !== undefined) {
        console.info(this.formatMessage('info', message), data);
      } else {
        console.info(this.formatMessage('info', message));
      }
    }
  }

  warn(message: string, data?: unknown): void {
    if (this.shouldLog('warn')) {
      if (data !== undefined) {
        console.warn(this.formatMessage('warn', message), data);
      } else {
        console.warn(this.formatMessage('warn', message));
      }
    }
  }

  error(message: string, error?: unknown): void {
    if (this.shouldLog('error')) {
      if (error !== undefined) {
        console.error(this.formatMessage('error', message), error);
      } else {
        console.error(this.formatMessage('error', message));
      }
    }
  }

  /**
   * Force log regardless of configuration (use sparingly)
   */
  forceLog(message: string, data?: unknown): void {
    console.log(`[FORCED] ${message}`, data !== undefined ? data : '');
  }
}

export const logger = new Logger();
