/**
 * Utility functions for localStorage with JSON support
 * Use localStorage for client-side persistence (survives page reloads)
 * Use sessionStorage if you want data to clear when tab is closed
 */

// Storage keys constants
export const STORAGE_KEYS = {
  TOKEN: 'token',
  USERNAME: 'username',
  ACCOUNT_TYPE: 'accountType',
  MEMBERSHIP_CACHE: 'membershipCache',
  FORM_DATA: 'formData',
  PAGE_STATE: 'pageState',
  RECENT_SEARCHES: 'recentProjectSearches',
} as const;

/**
 * Save data to localStorage (persists across sessions)
 */
export const saveToStorage = <T>(key: string, value: T): void => {
  try {
    const serialized = JSON.stringify(value);
    localStorage.setItem(key, serialized);
  } catch (error) {
    console.error(`Error saving to localStorage key "${key}":`, error);
  }
};

/**
 * Get data from localStorage
 */
export const getFromStorage = <T>(key: string, defaultValue: T | null = null): T | null => {
  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item) as T;
  } catch (error) {
    console.error(`Error reading from localStorage key "${key}":`, error);
    return defaultValue;
  }
};

/**
 * Remove data from localStorage
 */
export const removeFromStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing from localStorage key "${key}":`, error);
  }
};

/**
 * Clear all localStorage data (or specific prefix)
 */
export const clearStorage = (prefix?: string): void => {
  try {
    if (prefix) {
      // Remove only keys with the prefix
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith(prefix)) {
          localStorage.removeItem(key);
        }
      });
    } else {
      localStorage.clear();
    }
  } catch (error) {
    console.error('Error clearing localStorage:', error);
  }
};

/**
 * Save string directly (no JSON parsing) - for simple strings
 */
export const saveStringToStorage = (key: string, value: string): void => {
  try {
    localStorage.setItem(key, value);
  } catch (error) {
    console.error(`Error saving string to localStorage key "${key}":`, error);
  }
};

/**
 * Get string directly (no JSON parsing) - for simple strings
 */
export const getStringFromStorage = (key: string, defaultValue: string | null = null): string | null => {
  try {
    return localStorage.getItem(key) ?? defaultValue;
  } catch (error) {
    console.error(`Error reading string from localStorage key "${key}":`, error);
    return defaultValue;
  }
};

/**
 * Save to sessionStorage (clears when tab closes)
 */
export const saveToSession = <T>(key: string, value: T): void => {
  try {
    const serialized = JSON.stringify(value);
    sessionStorage.setItem(key, serialized);
  } catch (error) {
    console.error(`Error saving to sessionStorage key "${key}":`, error);
  }
};

/**
 * Get from sessionStorage
 */
export const getFromSession = <T>(key: string, defaultValue: T | null = null): T | null => {
  try {
    const item = sessionStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item) as T;
  } catch (error) {
    console.error(`Error reading from sessionStorage key "${key}":`, error);
    return defaultValue;
  }
};

