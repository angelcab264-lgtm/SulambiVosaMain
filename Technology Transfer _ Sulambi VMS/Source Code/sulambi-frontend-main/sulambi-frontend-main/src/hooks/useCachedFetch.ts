import { useState, useEffect, useCallback } from 'react';
import { getCachedResponse, setCachedResponse, getMemoryCache, setMemoryCache, CACHE_TIMES } from '../utils/apiCache';

interface UseCachedFetchOptions<T> {
  // Cache key (should be unique per request)
  cacheKey: string;
  // Function that returns the API call promise
  fetchFn: () => Promise<{ data: T }>;
  // Cache expiration time in milliseconds
  cacheTime?: number;
  // Use memory cache (faster, but clears on refresh) or localStorage (persists)
  useMemoryCache?: boolean;
  // Force refresh (skip cache)
  forceRefresh?: boolean;
  // Enable/disable cache
  enabled?: boolean;
}

interface UseCachedFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
  clearCache: () => void;
}

/**
 * Hook to fetch and cache API responses
 * Automatically uses cache when available, only fetches when needed
 * 
 * @example
 * const { data, loading, error, refetch } = useCachedFetch({
 *   cacheKey: 'events',
 *   fetchFn: () => getAllEvents(),
 *   cacheTime: CACHE_TIMES.MEDIUM, // 5 minutes
 * });
 */
export function useCachedFetch<T>({
  cacheKey,
  fetchFn,
  cacheTime = CACHE_TIMES.MEDIUM,
  useMemoryCache = true, // Use memory cache by default (faster)
  forceRefresh = false,
  enabled = true,
}: UseCachedFetchOptions<T>): UseCachedFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async (skipCache = false) => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    // Check cache first (unless force refresh or skip cache)
    if (!skipCache && !forceRefresh) {
      // Try memory cache first (faster)
      if (useMemoryCache) {
        const cached = getMemoryCache<T>(cacheKey);
        if (cached !== null) {
          setData(cached);
          setLoading(false);
          setError(null);
          return;
        }
      }

      // Try localStorage cache
      const cached = getCachedResponse<T>(cacheKey, cacheTime);
      if (cached !== null) {
        setData(cached);
        setLoading(false);
        setError(null);
        // Also put in memory cache for faster access
        if (useMemoryCache) {
          setMemoryCache(cacheKey, cached, cacheTime);
        }
        return;
      }
    }

    // No cache or force refresh - fetch from API
    setLoading(true);
    setError(null);

    try {
      const response = await fetchFn();
      const fetchedData = response.data;

      setData(fetchedData);
      setError(null);

      // Save to cache
      if (useMemoryCache) {
        setMemoryCache(cacheKey, fetchedData, cacheTime);
      }
      setCachedResponse(cacheKey, fetchedData, cacheTime);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      setData(null);
      console.error(`Error fetching data for cache key "${cacheKey}":`, error);
    } finally {
      setLoading(false);
    }
  }, [cacheKey, fetchFn, cacheTime, useMemoryCache, forceRefresh, enabled]);

  // Fetch on mount
  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey, enabled]); // Only refetch if cacheKey or enabled changes

  const refetch = useCallback(() => {
    fetchData(true); // Skip cache
  }, [fetchData]);

  const clearCache = useCallback(() => {
    const { removeCachedResponse, clearMemoryCache } = require('../utils/apiCache');
    if (useMemoryCache) {
      clearMemoryCache(cacheKey);
    }
    removeCachedResponse(cacheKey);
    setData(null);
  }, [cacheKey, useMemoryCache]);

  return {
    data,
    loading,
    error,
    refetch,
    clearCache,
  };
}


