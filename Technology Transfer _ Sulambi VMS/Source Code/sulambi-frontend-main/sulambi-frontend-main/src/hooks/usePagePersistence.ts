import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { saveToStorage, getFromStorage, removeFromStorage } from '../utils/storage';

/**
 * Hook to persist page-specific state across navigation
 * Each page gets its own storage key based on the route
 * Data persists when navigating away and returns when coming back
 * 
 * @example
 * // In DashboardPage component
 * const [filters, setFilters] = usePagePersistence('filters', {
 *   status: '',
 *   date: '',
 *   search: '',
 * });
 * // Filters will persist when you navigate away and come back!
 * 
 * @example
 * // In EventForm component
 * const [formData, setFormData] = usePagePersistence('form', {
 *   title: '',
 *   description: '',
 * });
 * // Form data persists across navigation!
 */
export function usePagePersistence<T>(
  key: string,
  defaultValue: T,
  options?: {
    // Clear data when component unmounts (on navigation away)
    clearOnUnmount?: boolean;
    // Debounce saving to avoid too many writes
    debounceMs?: number;
  }
): [T, (value: T | ((prev: T) => T)) => void] {
  const location = useLocation();
  const { clearOnUnmount = false, debounceMs } = options || {};
  
  // Create a unique key for this page + key combination
  const storageKey = `page_${location.pathname}_${key}`;
  
  // Initialize state from storage
  const [state, setState] = useState<T>(() => {
    try {
      const saved = getFromStorage<T>(storageKey, null);
      if (saved !== null) {
        return saved;
      }
    } catch (error) {
      console.error(`Error loading persisted state for "${storageKey}":`, error);
    }
    return defaultValue;
  });

  // Save to storage whenever state changes
  useEffect(() => {
    const save = () => {
      try {
        saveToStorage(storageKey, state);
      } catch (error) {
        console.error(`Error saving persisted state for "${storageKey}":`, error);
      }
    };

    if (debounceMs) {
      const timeoutId = setTimeout(save, debounceMs);
      return () => clearTimeout(timeoutId);
    } else {
      save();
    }
  }, [state, storageKey, debounceMs]);

  // Clear on unmount if requested
  useEffect(() => {
    if (clearOnUnmount) {
      return () => {
        removeFromStorage(storageKey);
      };
    }
  }, [clearOnUnmount, storageKey]);

  // Enhanced setter
  const setPersistedState = (value: T | ((prev: T) => T)) => {
    setState(value);
  };

  return [state, setPersistedState];
}

/**
 * Hook to persist state globally (across all pages)
 * Use this for app-wide settings, preferences, etc.
 * 
 * @example
 * const [userPreferences, setUserPreferences] = useGlobalPersistence('userPrefs', {
 *   theme: 'light',
 *   language: 'en',
 * });
 */
export function useGlobalPersistence<T>(
  key: string,
  defaultValue: T,
  options?: {
    debounceMs?: number;
  }
): [T, (value: T | ((prev: T) => T)) => void] {
  const { debounceMs } = options || {};
  
  // Use global key (no page path)
  const storageKey = `global_${key}`;
  
  // Initialize state from storage
  const [state, setState] = useState<T>(() => {
    try {
      const saved = getFromStorage<T>(storageKey, null);
      if (saved !== null) {
        return saved;
      }
    } catch (error) {
      console.error(`Error loading global state for "${storageKey}":`, error);
    }
    return defaultValue;
  });

  // Save to storage whenever state changes
  useEffect(() => {
    const save = () => {
      try {
        saveToStorage(storageKey, state);
      } catch (error) {
        console.error(`Error saving global state for "${storageKey}":`, error);
      }
    };

    if (debounceMs) {
      const timeoutId = setTimeout(save, debounceMs);
      return () => clearTimeout(timeoutId);
    } else {
      save();
    }
  }, [state, storageKey, debounceMs]);

  const setPersistedState = (value: T | ((prev: T) => T)) => {
    setState(value);
  };

  return [state, setPersistedState];
}

/**
 * Hook to clear persisted state for a specific page or key
 * Useful for cleanup on form submission or logout
 * 
 * @example
 * // Clear all data for current page
 * const clearPageData = useClearPagePersistence();
 * 
 * // On form submit
 * await submitForm();
 * clearPageData(); // Clears all persisted data for this page
 */
export function useClearPagePersistence() {
  const location = useLocation();

  return (key?: string) => {
    try {
      if (key) {
        // Clear specific key for this page
        const storageKey = `page_${location.pathname}_${key}`;
        removeFromStorage(storageKey);
      } else {
        // Clear all keys for this page
        const prefix = `page_${location.pathname}_`;
        Object.keys(localStorage).forEach((storageKey) => {
          if (storageKey.startsWith(prefix)) {
            removeFromStorage(storageKey);
          }
        });
      }
    } catch (error) {
      console.error('Error clearing page persistence:', error);
    }
  };
}

