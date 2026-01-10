# Data Persistence Scenarios

## Your Use Cases

Based on your clarification:
1. ✅ **Manual refresh (F5)** - Pages reload
2. ✅ **Data updates** - Pages reload after new data is fetched
3. ✅ **Navigation** - No reload (React Router handles this)

## How Each Scenario Works

### Scenario 1: Manual Refresh (F5) ✅

**What happens:**
- User is on `/admin/dashboard` with filters set
- User presses **F5** (refresh)
- Page reloads completely
- **localStorage persists data** ✅
- Data is restored automatically

**Solution:** ✅ Already working
- `FormDataProvider` auto-saves to localStorage
- `usePagePersistence` hook saves to localStorage
- Data loads on component mount

### Scenario 2: Data Updates (After API Call) ✅

**What happens:**
- User fills form or sets filters
- API call fetches new data
- Page reloads/refreshes to show new data
- **localStorage preserves user input** ✅
- Form data/filters are restored after reload

**Solution:** ✅ Already working
- localStorage saves before API call
- After reload, data is restored
- User sees their input + new data from API

**Important:** If you're clearing form data after API success, you might want to preserve it:

```tsx
// ❌ This clears data after API call
await submitForm(formData);
resetFormData(); // Data lost!

// ✅ This preserves data if needed
await submitForm(formData);
// Don't clear if user might want to edit again
// Or only clear on explicit user action
```

### Scenario 3: Navigation Between Pages ✅

**What happens:**
- User is on `/admin/dashboard` with filters
- User clicks link to `/admin/calendar`
- **No page reload** - React Router handles it
- Filters stay in localStorage
- User comes back to `/admin/dashboard`
- **Filters restored from localStorage** ✅

**Solution:** ✅ Already working
- `usePagePersistence` hook saves per route
- Data persists when navigating away
- Data restores when coming back

## Current Setup Status

✅ **All scenarios are covered!**

### What's Already Working:

1. **FormDataProvider** - Auto-saves form data
   - Saves on every change
   - Restores on page load (refresh or navigation)

2. **usePagePersistence hook** - Page-specific state
   - Saves to localStorage automatically
   - Restores when returning to page
   - Works for filters, search, etc.

3. **AccountDetailsProvider** - User account data
   - Already persists (token, username, accountType)
   - Survives refresh and navigation

## Best Practices for Your Use Cases

### For Manual Refresh (F5):

```tsx
// ✅ Good - Data persists
const [filters, setFilters] = usePagePersistence('filters', {
  status: '',
  date: '',
});

// User sets filters, presses F5
// Filters are restored! ✅
```

### For Data Updates (After API):

```tsx
function DashboardPage() {
  const [filters, setFilters] = usePagePersistence('filters', {
    status: '',
    date: '',
  });
  const [data, setData] = useState([]);

  // Fetch data with current filters
  useEffect(() => {
    fetchData(filters).then(setData);
  }, [filters]);

  // If page reloads after data update:
  // ✅ Filters are preserved
  // ✅ New data is fetched with preserved filters
}
```

### For Forms After API Submission:

```tsx
function EventForm() {
  const [formData, setFormData] = usePagePersistence('eventForm', {
    title: '',
    description: '',
  });

  const handleSubmit = async () => {
    await submitForm(formData);
    
    // Option 1: Clear after success (fresh start)
    clearPageData('eventForm');
    
    // Option 2: Keep data (user might edit again)
    // Don't clear - data persists
    
    // Option 3: Show success, then clear on navigation
    showSuccess();
    // Clear will happen on next navigation or refresh
  };
}
```

## Testing Your Scenarios

### Test 1: Manual Refresh
1. Go to `/admin/dashboard`
2. Set filters: `{ status: 'active', search: 'test' }`
3. Press **F5** (refresh)
4. **Expected:** Filters are still set ✅

### Test 2: Data Update Reload
1. Go to `/admin/dashboard`
2. Set filters
3. Trigger API call that causes reload
4. **Expected:** Filters are preserved, page reloads with new data ✅

### Test 3: Navigation
1. Go to `/admin/dashboard`
2. Set filters
3. Navigate to `/admin/calendar`
4. Navigate back to `/admin/dashboard`
5. **Expected:** Filters are still set ✅

## Important Notes

### ✅ What Persists:
- Form inputs (text, selects, checkboxes)
- Filters and search queries
- Table sort/pagination state
- User preferences per page
- Scroll position (if using `useScrollRestoration`)

### ❌ What Doesn't Persist (By Design):
- Component state that shouldn't persist (loading states, errors)
- Temporary UI state (modals, dropdowns)
- API response data (fetched fresh)

### When Data is Cleared:
- User logs out (should clear all user data)
- Form submission (optional - you decide)
- Explicit clear action by user
- Browser clears localStorage (rare, user action)

## Summary

✅ **Manual refresh (F5)** → localStorage restores data  
✅ **Data updates (API reload)** → localStorage preserves user input  
✅ **Navigation** → localStorage preserves per-page data  

**Your setup handles all three scenarios!** 🎉

The persistence system works exactly as needed for your use case where pages only reload on:
1. Manual refresh ✅
2. Data updates ✅

