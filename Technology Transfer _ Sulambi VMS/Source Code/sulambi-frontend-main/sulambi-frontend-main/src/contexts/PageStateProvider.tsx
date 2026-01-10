import { createContext, ReactNode, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { saveToStorage, getFromStorage, removeFromStorage } from '../utils/storage';

interface PageState {
  [key: string]: any;
}

interface PageStateContextValue {
  // Get state for current page
  getState: <T>(key: string, defaultValue: T) => T;
  // Set state for current page
  setState: <T>(key: string, value: T) => void;
  // Clear state for current page
  clearState: (key?: string) => void;
  // Get state for specific page (by path)
  getStateForPage: <T>(pagePath: string, key: string, defaultValue: T) => T;
}

export const PageStateContext = createContext<PageStateContextValue>({
  getState: () => null,
  setState: () => {},
  clearState: () => {},
  getStateForPage: () => null,
});

interface PageStateProviderProps {
  children: ReactNode;
}

/**
 * Provider that manages page-specific state persistence
 * State persists when navigating away and restores when returning
 * 
 * Usage:
 * - Wrap your app with this provider (inside BrowserRouter)
 * - Use the context to save/load page-specific state
 * - State automatically persists per route
 */
export const PageStateProvider = ({ children }: PageStateProviderProps) => {
  const location = useLocation();
  const [state, setState] = useState<PageState>({});

  // Load state for current page on mount/navigation
  useEffect(() => {
    const loadPageState = () => {
      try {
        const pageStateKey = `pageState_${location.pathname}`;
        const saved = getFromStorage<PageState>(pageStateKey, {});
        setState(saved || {});
      } catch (error) {
        console.error('Error loading page state:', error);
        setState({});
      }
    };

    loadPageState();
  }, [location.pathname]);

  // Save state whenever it changes
  useEffect(() => {
    if (Object.keys(state).length > 0) {
      try {
        const pageStateKey = `pageState_${location.pathname}`;
        saveToStorage(pageStateKey, state);
      } catch (error) {
        console.error('Error saving page state:', error);
      }
    }
  }, [state, location.pathname]);

  const getState = <T,>(key: string, defaultValue: T): T => {
    return (state[key] !== undefined ? state[key] : defaultValue) as T;
  };

  const setStateForKey = <T,>(key: string, value: T) => {
    setState((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const clearState = (key?: string) => {
    try {
      if (key) {
        // Clear specific key
        setState((prev) => {
          const updated = { ...prev };
          delete updated[key];
          return updated;
        });
      } else {
        // Clear all state for current page
        const pageStateKey = `pageState_${location.pathname}`;
        removeFromStorage(pageStateKey);
        setState({});
      }
    } catch (error) {
      console.error('Error clearing page state:', error);
    }
  };

  const getStateForPage = <T,>(pagePath: string, key: string, defaultValue: T): T => {
    try {
      const pageStateKey = `pageState_${pagePath}`;
      const pageState = getFromStorage<PageState>(pageStateKey, {});
      return (pageState[key] !== undefined ? pageState[key] : defaultValue) as T;
    } catch (error) {
      console.error('Error loading state for page:', error);
      return defaultValue;
    }
  };

  return (
    <PageStateContext.Provider
      value={{
        getState,
        setState: setStateForKey,
        clearState,
        getStateForPage,
      }}
    >
      {children}
    </PageStateContext.Provider>
  );
};

