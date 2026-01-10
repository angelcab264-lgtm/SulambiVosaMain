import { useState, useEffect } from 'react';
import { saveToStorage, getFromStorage } from '../utils/storage';

/**
 * Hook to persist state in localStorage and restore it on reload
 * 
 * @example
 * // Persist form data
 * const [formData, setFormData] = usePersistedState('myForm', {});
 * 
 * // Persist page filters
 * const [filters, setFilters] = usePersistedState('dashboardFilters', { date: '', status: '' });
 * 
 * // Persist with custom storage key
 * const [preferences, setPreferences] = usePersistedState<UserPreferences>(
 *   'userPreferences',
 *   { theme: 'light', language: 'en' }
 * );
 */
export function usePersistedState<T>(
  storageKey: string,
  defaultValue: T,
  options?: {
    // Use sessionStorage instead of localStorage (clears on tab close)
    useSession?: boolean;
    // Only save when value actually changes (debounce)
    debounceMs?: number;
  }
): [T, (value: T | ((prev: T) => T)) => void] {
  const { useSession = false, debounceMs } = options || {};

  // Initialize state from storage or use default
  const [state, setState] = useState<T>(() => {
    try {
      if (useSession) {
        const item = sessionStorage.getItem(storageKey);
        if (item) {
          return JSON.parse(item) as T;
        }
      } else {
        const item = localStorage.getItem(storageKey);
        if (item) {
          return JSON.parse(item) as T;
        }
      }
    } catch (error) {
      console.error(`Error loading persisted state for "${storageKey}":`, error);
    }
    return defaultValue;
  });

  // Save to storage whenever state changes
  useEffect(() => {
    const save = () => {
      if (useSession) {
        sessionStorage.setItem(storageKey, JSON.stringify(state));
      } else {
        localStorage.setItem(storageKey, JSON.stringify(state));
      }
    };

    if (debounceMs) {
      const timeoutId = setTimeout(save, debounceMs);
      return () => clearTimeout(timeoutId);
    } else {
      save();
    }
  }, [state, storageKey, useSession, debounceMs]);

  // Enhanced setter that handles both direct values and updater functions
  const setPersistedState = (value: T | ((prev: T) => T)) => {
    setState(value);
  };

  return [state, setPersistedState];
}

