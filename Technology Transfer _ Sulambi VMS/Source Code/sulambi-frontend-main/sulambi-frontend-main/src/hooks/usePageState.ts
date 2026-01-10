import { useEffect } from 'react';
import { saveToStorage, getFromStorage } from '../utils/storage';

/**
 * Hook to persist page-specific state (scroll position, filters, etc.)
 * Automatically saves and restores on page reload
 * 
 * @example
 * // Persist scroll position
 * usePageState('dashboardScroll', window.scrollY, (value) => {
 *   window.scrollTo(0, value);
 * });
 * 
 * // Persist filters
 * const [filters, setFilters] = useState(() => 
 *   getFromStorage('dashboardFilters', { status: '', date: '' })
 * );
 * usePageState('dashboardFilters', filters);
 * 
 * // Persist form data
 * const [formData, setFormData] = useState(() =>
 *   getFromStorage('eventFormData', {})
 * );
 * usePageState('eventFormData', formData);
 */
export function usePageState<T>(
  storageKey: string,
  value: T,
  onRestore?: (restoredValue: T) => void
): void {
  // Save whenever value changes
  useEffect(() => {
    saveToStorage(storageKey, value);
  }, [storageKey, value]);

  // Restore on mount (only once)
  useEffect(() => {
    const restored = getFromStorage<T>(storageKey, null);
    if (restored !== null && onRestore) {
      onRestore(restored);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount
}

/**
 * Hook to persist scroll position and restore on reload
 * 
 * @example
 * // In any page component
 * useScrollRestoration('dashboard-page');
 */
export function useScrollRestoration(key: string): void {
  useEffect(() => {
    // Save scroll position before unload
    const saveScroll = () => {
      saveToStorage(`scroll_${key}`, {
        x: window.scrollX,
        y: window.scrollY,
      });
    };

    // Restore scroll position
    const restoreScroll = () => {
      const saved = getFromStorage<{ x: number; y: number }>(`scroll_${key}`, null);
      if (saved) {
        window.scrollTo(saved.x, saved.y);
      }
    };

    // Save on scroll (throttled)
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          saveScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    // Restore on mount
    restoreScroll();

    // Listen for scroll events
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Save on page unload
    window.addEventListener('beforeunload', saveScroll);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('beforeunload', saveScroll);
    };
  }, [key]);
}

