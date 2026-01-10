/**
 * API Response Caching Utility
 * Caches API responses to avoid re-fetching when navigating back to pages
 */

import { saveToStorage, getFromStorage } from './storage';

interface CachedResponse<T> {
  data: T;
  timestamp: number;
  expiresIn?: number; // milliseconds
}

// Cache expiration times (in milliseconds)
export const CACHE_TIMES = {
  SHORT: 30 * 1000,      // 30 seconds
  MEDIUM: 5 * 60 * 1000, // 5 minutes
  LONG: 30 * 60 * 1000,  // 30 minutes
  VERY_LONG: 60 * 60 * 1000, // 1 hour
} as const;

/**
 * Get cached API response if it exists and is not expired
 */
export function getCachedResponse<T>(
  cacheKey: string,
  maxAge: number = CACHE_TIMES.MEDIUM
): T | null {
  try {
    const cached = getFromStorage<CachedResponse<T>>(`api_cache_${cacheKey}`, null);
    
    if (!cached) {
      return null;
    }

    const age = Date.now() - cached.timestamp;
    const expiresIn = cached.expiresIn || maxAge;

    // Check if cache is expired
    if (age > expiresIn) {
      // Cache expired, remove it
      removeCachedResponse(cacheKey);
      return null;
    }

    return cached.data;
  } catch (error) {
    console.error(`Error reading cache for "${cacheKey}":`, error);
    return null;
  }
}

/**
 * Save API response to cache
 */
export function setCachedResponse<T>(
  cacheKey: string,
  data: T,
  expiresIn?: number
): void {
  try {
    const cached: CachedResponse<T> = {
      data,
      timestamp: Date.now(),
      expiresIn,
    };
    saveToStorage(`api_cache_${cacheKey}`, cached);
  } catch (error) {
    console.error(`Error saving cache for "${cacheKey}":`, error);
  }
}

/**
 * Remove cached response
 */
export function removeCachedResponse(cacheKey: string): void {
  try {
    const { removeFromStorage } = require('./storage');
    removeFromStorage(`api_cache_${cacheKey}`);
  } catch (error) {
    console.error(`Error removing cache for "${cacheKey}":`, error);
  }
}

/**
 * Clear all API caches
 */
export function clearAllApiCache(): void {
  try {
    const { clearStorage } = require('./storage');
    clearStorage('api_cache_');
  } catch (error) {
    console.error('Error clearing API cache:', error);
  }
}

/**
 * In-memory cache for faster access (clears on page refresh)
 */
const memoryCache = new Map<string, { data: any; timestamp: number; expiresIn?: number }>();

/**
 * Get from memory cache (faster than localStorage)
 */
export function getMemoryCache<T>(key: string): T | null {
  const cached = memoryCache.get(key);
  if (!cached) return null;

  const age = Date.now() - cached.timestamp;
  const expiresIn = cached.expiresIn || CACHE_TIMES.MEDIUM;

  if (age > expiresIn) {
    memoryCache.delete(key);
    return null;
  }

  return cached.data as T;
}

/**
 * Set memory cache
 */
export function setMemoryCache<T>(key: string, data: T, expiresIn?: number): void {
  memoryCache.set(key, {
    data,
    timestamp: Date.now(),
    expiresIn,
  });
}

/**
 * Clear memory cache
 */
export function clearMemoryCache(key?: string): void {
  if (key) {
    memoryCache.delete(key);
  } else {
    memoryCache.clear();
  }
}


