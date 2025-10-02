/**
 * User Interaction Logging Service for ShambaAI Frontend
 * Handles logging of user interactions, page views, and errors
 */

// Simple UUID generator (alternative to uuid package)
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Types for logging
export interface LoggingConfig {
  enabled: boolean;
  apiEndpoint: string;
  sessionId: string;
  userId?: string;
}

export interface InteractionLog {
  interactionType: string;
  pageName: string;
  actionName: string;
  resourceType?: string;
  resourceId?: string;
  inputData?: any;
  outputData?: any;
  responseTimeMs?: number;
  successStatus: boolean;
  errorMessage?: string;
}

export interface PageViewLog {
  pageName: string;
  pageUrl: string;
  pageTitle: string;
  viewDurationSeconds?: number;
  scrollDepthPct?: number;
  elementsClicked?: string[];
  formsInteracted?: string[];
}

export interface ErrorLog {
  errorType: string;
  errorCategory: string;
  errorMessage: string;
  errorStack?: string;
  errorSource: string;
  userAction?: string;
  browserInfo?: any;
}

// Interaction types
export const InteractionType = {
  ASK_QUESTION: 'ASK_QUESTION',
  GET_INSIGHTS: 'GET_INSIGHTS',
  VIEW_ABOUT: 'VIEW_ABOUT',
  VIEW_ADMIN: 'VIEW_ADMIN',
  LOGIN: 'LOGIN',
  LOGOUT: 'LOGOUT',
  NAVIGATE: 'NAVIGATE',
  SEARCH: 'SEARCH',
  DOWNLOAD: 'DOWNLOAD',
  UPLOAD: 'UPLOAD',
  EXPORT: 'EXPORT',
  SHARE: 'SHARE'
} as const;

// Page names
export const PageName = {
  HOME: 'home',
  ABOUT: 'about',
  ASK: 'ask',
  INSIGHTS: 'insights',
  ADMIN: 'admin',
  LOGIN: 'login',
  ERROR: 'error'
} as const;

// Feature categories
export const FeatureCategory = {
  AI: 'AI',
  ANALYTICS: 'Analytics',
  CONTENT: 'Content',
  AUTHENTICATION: 'Authentication',
  NAVIGATION: 'Navigation',
  DATA_MANAGEMENT: 'Data Management',
  REPORTING: 'Reporting'
} as const;

class UserLoggingService {
  private config: LoggingConfig;
  private sessionId: string;
  private userId?: string;
  private pageViewStartTime: number = 0;
  private scrollDepth: number = 0;
  private maxScrollDepth: number = 0;
  private clickedElements: Set<string> = new Set();
  private formInteractions: Set<string> = new Set();

  constructor(config: LoggingConfig) {
    this.config = config;
    this.sessionId = config.sessionId || this.generateSessionId();
    this.userId = config.userId;
    
    if (this.config.enabled) {
      this.initializeLogging();
    }
  }

  private generateSessionId(): string {
    return `session_${generateUUID()}`;
  }

  private initializeLogging(): void {
    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.logPageExit();
      } else {
        this.logPageEnter();
      }
    });

    // Track scroll depth
    let scrollTimeout: NodeJS.Timeout;
    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.updateScrollDepth();
      }, 100);
    });

    // Track element clicks
    document.addEventListener('click', (event) => {
      this.trackElementClick(event);
    });

    // Track form interactions
    document.addEventListener('input', (event) => {
      this.trackFormInteraction(event);
    });

    // Track page unload
    window.addEventListener('beforeunload', () => {
      this.logPageExit();
    });

    // Track errors
    window.addEventListener('error', (event) => {
      this.logError({
        errorType: 'JavaScript',
        errorCategory: 'Runtime',
        errorMessage: event.message,
        errorStack: event.error?.stack,
        errorSource: 'frontend',
        userAction: 'page_interaction'
      });
    });

    // Track unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        errorType: 'Promise',
        errorCategory: 'Unhandled',
        errorMessage: event.reason?.message || 'Unhandled promise rejection',
        errorStack: event.reason?.stack,
        errorSource: 'frontend',
        userAction: 'async_operation'
      });
    });
  }

  public setUserId(userId: string): void {
    this.userId = userId;
  }

  public clearUserId(): void {
    this.userId = undefined;
  }

  public logInteraction(log: InteractionLog): void {
    try {
      if (!this.config.enabled) return;

      const payload = {
        interactionType: log.interactionType,
        pageName: log.pageName,
        actionName: log.actionName,
        resourceType: log.resourceType,
        resourceId: log.resourceId,
        inputData: log.inputData,
        outputData: log.outputData,
        responseTimeMs: log.responseTimeMs,
        successStatus: log.successStatus,
        errorMessage: log.errorMessage,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        userId: this.userId
      };

      this.sendLog('interaction', payload);
    } catch (error) {
      console.warn('Failed to log interaction:', error);
    }
  }

  public logPageView(pageName: string, pageTitle?: string): void {
    try {
      if (!this.config.enabled) return;

      this.logPageExit(); // Log previous page exit if any
      this.currentPage = pageName;
      this.pageViewStartTime = Date.now();
      this.scrollDepth = 0;
      this.maxScrollDepth = 0;
      this.clickedElements.clear();
      this.formInteractions.clear();

      const payload: PageViewLog = {
        pageName,
        pageUrl: window.location.href,
        pageTitle: pageTitle || document.title
      };

      this.sendLog('page-view', payload);
    } catch (error) {
      console.warn('Failed to log page view:', error);
    }
  }

  private logPageEnter(): void {
    this.pageViewStartTime = Date.now();
  }

  private logPageExit(): void {
    if (this.pageViewStartTime === 0) return;

    const viewDuration = Math.round((Date.now() - this.pageViewStartTime) / 1000);
    
    const payload = {
      pageName: this.getCurrentPageName(),
      pageUrl: window.location.href,
      pageTitle: document.title,
      viewDurationSeconds: viewDuration,
      scrollDepthPct: this.maxScrollDepth,
      elementsClicked: Array.from(this.clickedElements),
      formsInteracted: Array.from(this.formInteractions)
    };

    this.sendLog('page-exit', payload);
    this.pageViewStartTime = 0;
  }

  public logError(error: ErrorLog): void {
    if (!this.config.enabled) return;

    const payload = {
      ...error,
      pageUrl: window.location.href,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      userId: this.userId,
      browserInfo: this.getBrowserInfo()
    };

    this.sendLog('error', payload);
  }

  public logFeatureUsage(
    featureName: string,
    featureCategory: string,
    success: boolean = true,
    timeSpentSeconds?: number
  ): void {
    if (!this.config.enabled) return;

    const payload = {
      featureName,
      featureCategory,
      success,
      timeSpentSeconds,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      userId: this.userId
    };

    this.sendLog('feature-usage', payload);
  }

  private updateScrollDepth(): void {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollDepth = scrollHeight > 0 ? Math.round((scrollTop / scrollHeight) * 100) : 0;
    
    this.scrollDepth = scrollDepth;
    this.maxScrollDepth = Math.max(this.maxScrollDepth, scrollDepth);
  }

  private trackElementClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target) return;

    const elementInfo = this.getElementInfo(target);
    this.clickedElements.add(elementInfo);
  }

  private trackFormInteraction(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target) return;

    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
      const formInfo = this.getFormInfo(target);
      this.formInteractions.add(formInfo);
    }
  }

  private getElementInfo(element: HTMLElement): string {
    const tagName = element.tagName.toLowerCase();
    const id = element.id ? `#${element.id}` : '';
    const className = element.className ? `.${element.className.split(' ').join('.')}` : '';
    const text = element.textContent?.substring(0, 50) || '';
    
    return `${tagName}${id}${className} - ${text}`;
  }

  private getFormInfo(element: HTMLElement): string {
    const tagName = element.tagName.toLowerCase();
    const type = element.getAttribute('type') || '';
    const name = element.getAttribute('name') || '';
    const id = element.id || '';
    
    return `${tagName}[${type}] ${name || id}`;
  }

  private getCurrentPageName(): string {
    const path = window.location.pathname;
    if (path === '/' || path === '/about') return PageName.ABOUT;
    if (path === '/ask') return PageName.ASK;
    if (path === '/insights') return PageName.INSIGHTS;
    if (path === '/admin') return PageName.ADMIN;
    if (path === '/login') return PageName.LOGIN;
    return PageName.HOME;
  }

  private getBrowserInfo(): any {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      screenWidth: screen.width,
      screenHeight: screen.height,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
  }

  private async sendLog(type: string, payload: any): Promise<void> {
    try {
      // For now, we'll store logs locally and send them in batches
      // In production, you might want to send them immediately or use a queue
      const logs = JSON.parse(localStorage.getItem('shamba_logs') || '[]');
      logs.push({ type, payload, timestamp: Date.now() });
      
      // Keep only last 100 logs to prevent storage overflow
      if (logs.length > 100) {
        logs.splice(0, logs.length - 100);
      }
      
      localStorage.setItem('shamba_logs', JSON.stringify(logs));

      // Send to backend if configured
      if (this.config.apiEndpoint) {
        await this.sendToBackend(type, payload);
      }
    } catch (error) {
      console.error('Failed to log interaction:', error);
    }
  }

  private async sendToBackend(type: string, payload: any): Promise<void> {
    try {
      const response = await fetch(`${this.config.apiEndpoint}/logs/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('shambaai_token') || ''}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        console.warn('Failed to send log to backend:', response.statusText);
      }
    } catch (error) {
      console.warn('Failed to send log to backend:', error);
    }
  }

  public async flushLogs(): Promise<void> {
    const logs = JSON.parse(localStorage.getItem('shamba_logs') || '[]');
    if (logs.length === 0) return;

    try {
      // Send all pending logs
      for (const log of logs) {
        await this.sendToBackend(log.type, log.payload);
      }

      // Clear local logs
      localStorage.removeItem('shamba_logs');
    } catch (error) {
      console.error('Failed to flush logs:', error);
    }
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public isEnabled(): boolean {
    return this.config.enabled;
  }

  public logError(error: ErrorLog): void {
    try {
      if (!this.config.enabled) return;

      const payload = {
        errorType: error.errorType,
        errorMessage: error.errorMessage,
        errorStack: error.errorStack,
        errorSource: error.errorSource,
        pageUrl: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        userId: this.userId
      };

      this.sendLog('error', payload);
    } catch (e) {
      console.warn('Failed to log error:', e);
    }
  }

  public logFeatureUsage(featureName: string, featureCategory: string, success?: boolean, timeSpentSeconds?: number): void {
    try {
      if (!this.config.enabled) return;

      const payload = {
        featureName,
        featureCategory,
        success,
        timeSpentSeconds,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        userId: this.userId
      };

      this.sendLog('feature-usage', payload);
    } catch (e) {
      console.warn('Failed to log feature usage:', e);
    }
  }
}

// Create global instance with comprehensive error handling
let loggingService: UserLoggingService;

// Safe localStorage access
const safeLocalStorage = {
  getItem: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.warn('localStorage access failed:', error);
      return null;
    }
  },
  setItem: (key: string, value: string): void => {
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      console.warn('localStorage write failed:', error);
    }
  }
};

try {
  loggingService = new UserLoggingService({
    enabled: true, // Enable logging with proper error handling
    apiEndpoint: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    sessionId: safeLocalStorage.getItem('shamba_session_id') || ''
  });
  
  // Store session ID in localStorage safely
  safeLocalStorage.setItem('shamba_session_id', loggingService.getSessionId());
} catch (error) {
  console.warn('Failed to initialize logging service:', error);
  // Create a dummy service that does nothing but doesn't throw errors
  loggingService = {
    logInteraction: (log: InteractionLog) => {
      try {
        console.log('Logging interaction:', log);
      } catch (e) {
        console.warn('Logging failed:', e);
      }
    },
    logPageView: (pageName: string, pageTitle?: string) => {
      try {
        console.log('Logging page view:', pageName, pageTitle);
      } catch (e) {
        console.warn('Page view logging failed:', e);
      }
    },
    logError: (error: ErrorLog) => {
      try {
        console.error('Logging error:', error);
      } catch (e) {
        console.warn('Error logging failed:', e);
      }
    },
    logFeatureUsage: (featureName: string, featureCategory: string, success?: boolean, timeSpentSeconds?: number) => {
      try {
        console.log('Logging feature usage:', featureName, featureCategory, success, timeSpentSeconds);
      } catch (e) {
        console.warn('Feature usage logging failed:', e);
      }
    },
    setUserId: (userId: string) => {
      try {
        console.log('Setting user ID:', userId);
      } catch (e) {
        console.warn('Set user ID failed:', e);
      }
    },
    clearUserId: () => {
      try {
        console.log('Clearing user ID');
      } catch (e) {
        console.warn('Clear user ID failed:', e);
      }
    },
    getSessionId: () => 'dummy-session',
    isEnabled: () => false
  } as any;
}

// Export convenience functions
export const logInteraction = (log: InteractionLog) => loggingService.logInteraction(log);
export const logPageView = (pageName: string, pageTitle?: string) => loggingService.logPageView(pageName, pageTitle);
export const logError = (error: ErrorLog) => loggingService.logError(error);
export const logFeatureUsage = (featureName: string, featureCategory: string, success?: boolean, timeSpentSeconds?: number) => 
  loggingService.logFeatureUsage(featureName, featureCategory, success, timeSpentSeconds);

export const setUserId = (userId: string) => loggingService.setUserId(userId);
export const clearUserId = () => loggingService.clearUserId();
export const flushLogs = () => loggingService.flushLogs();

// Export the service instance
export default loggingService;
