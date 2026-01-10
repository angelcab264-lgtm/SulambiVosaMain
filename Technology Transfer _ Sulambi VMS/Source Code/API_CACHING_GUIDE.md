# API Caching Guide - Prevent Reloading on Navigation

## Problem

When you navigate away from a page and come back, the page reloads and fetches data again, even though nothing changed.

## Solution

Use **API response caching** to store fetched data so it doesn't need to refetch when navigating back.

## How It Works

### Two-Level Caching:

1. **Memory Cache** (Fast) - Clears on page refresh
   - Super fast access
   - Used for navigation (switching tabs)
   - Clears when browser tab closes

2. **localStorage Cache** (Persistent) - Survives page refresh
   - Persists after page refresh (F5)
   - Used as backup when memory cache is empty
   - Can be configured to expire after a certain time

## Quick Usage

### Option 1: Use the Hook (Easiest)

```tsx
import { useCachedFetch } from '../hooks/useCachedFetch';
import { CACHE_TIMES } from '../utils/apiCache';

function EventsPage() {
  const { data, loading, error } = useCachedFetch({
    cacheKey: 'events_all',
    fetchFn: () => getAllEvents(),
    cacheTime: CACHE_TIMES.MEDIUM, // 5 minutes
  });

  // Data is cached! Navigate away and come back - no reload! ✅
}
```

### Option 2: Manual Caching

```tsx
import { getCachedResponse, setCachedResponse, CACHE_TIMES } from '../utils/apiCache';

function MyPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check cache first
    const cached = getCachedResponse('my_data_key', CACHE_TIMES.MEDIUM);
    if (cached) {
      setData(cached);
      setLoading(false);
      return; // Use cache, don't fetch
    }

    // No cache - fetch from API
    fetchMyData()
      .then((response) => {
        setData(response.data);
        // Save to cache
        setCachedResponse('my_data_key', response.data, CACHE_TIMES.MEDIUM);
      })
      .finally(() => setLoading(false));
  }, []);
}
```

## Cache Times

```tsx
import { CACHE_TIMES } from '../utils/apiCache';

CACHE_TIMES.SHORT      // 30 seconds
CACHE_TIMES.MEDIUM     // 5 minutes (recommended for most data)
CACHE_TIMES.LONG       // 30 minutes
CACHE_TIMES.VERY_LONG  // 1 hour
```

## Examples

### Example 1: Events Page (Already Updated)

```tsx
const { data: eventsResponse, loading } = useCachedFetch({
  cacheKey: 'events_all',
  fetchFn: () => getAllEvents(),
  cacheTime: CACHE_TIMES.MEDIUM,
});

// Navigate away, come back - instant load from cache! ✅
```

### Example 2: Dashboard Data

```tsx
const { data: dashboardData, loading } = useCachedFetch({
  cacheKey: 'dashboard_summary',
  fetchFn: () => getDashboardSummary(),
  cacheTime: CACHE_TIMES.SHORT, // Refresh every 30 seconds
});
```

### Example 3: User Profile (Long Cache)

```tsx
const { data: userProfile, loading } = useCachedFetch({
  cacheKey: 'user_profile',
  fetchFn: () => getUserProfile(),
  cacheTime: CACHE_TIMES.LONG, // Cache for 30 minutes
});
```

### Example 4: With Manual Refresh Button

```tsx
const { data, loading, refetch } = useCachedFetch({
  cacheKey: 'events',
  fetchFn: () => getAllEvents(),
  cacheTime: CACHE_TIMES.MEDIUM,
});

// Add refresh button
<button onClick={refetch}>Refresh Data</button>
```

### Example 5: Clear Cache on Action

```tsx
const { data, loading, clearCache } = useCachedFetch({
  cacheKey: 'events',
  fetchFn: () => getAllEvents(),
});

const handleCreateEvent = async () => {
  await createEvent(newEvent);
  clearCache(); // Clear cache so it refetches with new data
};
```

## When to Use

### ✅ Use Caching For:
- **Events list** - Doesn't change often
- **Dashboard data** - Can be slightly stale
- **User profile** - Rarely changes
- **Reports** - Expensive to fetch
- **Tables/Lists** - Static or slow-changing data

### ❌ Don't Cache:
- **Real-time data** - Stock prices, live chats
- **Form submissions** - Always fetch fresh
- **Search results** - User wants current results
- **User actions** - Need immediate updates

## Advanced Options

```tsx
const { data, loading, refetch, clearCache } = useCachedFetch({
  cacheKey: 'events',
  fetchFn: () => getAllEvents(),
  cacheTime: CACHE_TIMES.MEDIUM,
  useMemoryCache: true,  // Use fast memory cache
  forceRefresh: false,   // Set to true to skip cache
  enabled: true,         // Enable/disable fetching
});

// Manual operations
refetch();      // Force fetch (skip cache)
clearCache();   // Clear cache for this key
```

## Clearing Cache

### Clear Specific Cache

```tsx
import { removeCachedResponse } from '../utils/apiCache';

// Clear specific cache
removeCachedResponse('events_all');
```

### Clear All Caches

```tsx
import { clearAllApiCache } from '../utils/apiCache';

// Clear all API caches (on logout, for example)
clearAllApiCache();
```

### Clear Memory Cache Only

```tsx
import { clearMemoryCache } from '../utils/apiCache';

clearMemoryCache('events'); // Clear specific key
clearMemoryCache();         // Clear all
```

## Testing

### Test Navigation Caching:

1. **Go to Events page** → Wait for data to load
2. **Navigate to Dashboard** → Data stays in memory cache
3. **Navigate back to Events** → Should load instantly (no spinner!)
4. **Result:** Instant load from cache ✅

### Test Refresh Caching:

1. **Load Events page** → Data is cached
2. **Press F5** (refresh)
3. **Page loads** → Should load from localStorage cache (fast!)
4. **Result:** Fast load from cache ✅

### Test Cache Expiration:

1. **Load Events page**
2. **Wait 6 minutes** (if using MEDIUM cache)
3. **Navigate back**
4. **Result:** Fetches fresh data (cache expired) ✅

## Best Practices

### ✅ DO:
- **Use unique cache keys** - `'events_all'` not just `'events'`
- **Choose appropriate cache times** - Don't cache too long for dynamic data
- **Clear cache after mutations** - After creating/updating/deleting
- **Use memory cache for navigation** - Faster access

### ❌ DON'T:
- **Cache sensitive data** - Passwords, tokens (already handled separately)
- **Cache too aggressively** - User might not see updates
- **Cache search/filter results** - User wants fresh results
- **Forget to clear cache** - After data changes

## Already Updated

✅ **EventsPage** - Now uses `useCachedFetch` hook

### Other Pages You Can Update:

- `DashboardPage` - Dashboard summary
- `CalendarPage` - Calendar events
- `ReportPage` - Reports list
- `AccountsPage` - Accounts list
- `EventApprovalPage` - Events for approval

## Performance Benefits

✅ **Faster navigation** - Instant load from cache  
✅ **Reduced API calls** - Less server load  
✅ **Better UX** - No loading spinners when navigating  
✅ **Offline capability** - Shows cached data if API fails  

## Summary

Use `useCachedFetch` hook for any page that fetches data:
- ✅ Prevents reload on navigation
- ✅ Fast memory cache for switching tabs
- ✅ Persistent cache for page refresh
- ✅ Automatic expiration
- ✅ Easy to use

**Your events page is now updated and won't reload when navigating back!** 🎉


