# State Persistence Guide - Keep Page Contents After Reload

This guide shows you how to persist page contents, form data, and app state after page reload using **localStorage** (client-side storage).

## Why localStorage instead of cookies?

- ✅ **Larger storage** (5-10MB vs 4KB for cookies)
- ✅ **No network overhead** (cookies are sent with every request)
- ✅ **Easy to use** (simple API)
- ✅ **Survives page reloads** (data persists until explicitly cleared)
- ✅ **Secure** (client-side only, can't be accessed by server unless you send it)

## What's Already Set Up

✅ **Authentication state** - Already persisted (token, username, accountType)  
✅ **Storage utilities** - Created in `src/utils/storage.ts`  
✅ **React hooks** - Created in `src/hooks/usePersistedState.ts` and `usePageState.ts`  
✅ **Enhanced contexts** - FormDataProvider and AccountDetailsProvider now auto-save

## How to Use

### 1. Persist Form Data (Easiest)

The `FormDataProvider` now automatically saves and restores form data:

```tsx
// In any component using FormDataContext
import { useContext } from 'react';
import { FormDataContext } from '../contexts/FormDataProvider';

function MyForm() {
  const { formData, setFormData } = useContext(FormDataContext);
  
  // Form data is automatically saved to localStorage
  // When page reloads, it will be restored automatically
  
  return (
    <input
      value={formData.name || ''}
      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
    />
  );
}
```

### 2. Persist Page State (Filters, Search, etc.)

Use the `usePersistedState` hook:

```tsx
import { usePersistedState } from '../hooks/usePersistedState';

function DashboardPage() {
  // Filters will persist after page reload
  const [filters, setFilters] = usePersistedState('dashboardFilters', {
    status: '',
    date: '',
    search: '',
  });

  return (
    <div>
      <input
        value={filters.search}
        onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        placeholder="Search..."
      />
      {/* Filters are automatically saved and restored */}
    </div>
  );
}
```

### 3. Persist Scroll Position

Restore scroll position after reload:

```tsx
import { useScrollRestoration } from '../hooks/usePageState';

function EventsPage() {
  // Automatically saves and restores scroll position
  useScrollRestoration('events-page');

  return (
    <div>
      {/* Long content */}
    </div>
  );
}
```

### 4. Manual Storage Operations

Use the storage utilities directly:

```tsx
import { saveToStorage, getFromStorage, removeFromStorage } from '../utils/storage';

// Save data
saveToStorage('myKey', { name: 'John', age: 30 });

// Get data
const data = getFromStorage('myKey', { name: '', age: 0 }); // with default

// Remove data
removeFromStorage('myKey');

// Clear all data with a prefix
clearStorage('myPrefix'); // Removes all keys starting with 'myPrefix'
```

### 5. Persist Component State

For any component state you want to persist:

```tsx
import { useState, useEffect } from 'react';
import { saveToStorage, getFromStorage } from '../utils/storage';

function MyComponent() {
  const [myState, setMyState] = useState(() => {
    // Initialize from localStorage
    return getFromStorage('myComponentState', { value: '' });
  });

  // Save whenever state changes
  useEffect(() => {
    saveToStorage('myComponentState', myState);
  }, [myState]);

  return <div>{/* Your component */}</div>;
}
```

### 6. Use SessionStorage (Clears on Tab Close)

For temporary data that should clear when tab closes:

```tsx
import { usePersistedState } from '../hooks/usePersistedState';

function MyComponent() {
  // This will clear when the browser tab is closed
  const [tempData, setTempData] = usePersistedState(
    'tempData',
    {},
    { useSession: true }
  );

  return <div>{/* Your component */}</div>;
}
```

## Examples

### Example 1: Dashboard Filters

```tsx
// src/pages/Admin/DashboardPage.tsx
import { usePersistedState } from '../../../hooks/usePersistedState';

function DashboardPage() {
  const [filters, setFilters] = usePersistedState('dashboardFilters', {
    status: 'all',
    dateFrom: '',
    dateTo: '',
    searchQuery: '',
  });

  // Filters will persist after reload!
  return (
    <div>
      <select
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
      >
        <option value="all">All</option>
        <option value="active">Active</option>
        <option value="completed">Completed</option>
      </select>
    </div>
  );
}
```

### Example 2: Form with Auto-Save

```tsx
// Any form component
import { usePersistedState } from '../hooks/usePersistedState';

function EventForm() {
  const [formData, setFormData] = usePersistedState('eventForm', {
    title: '',
    description: '',
    date: '',
    location: '',
  });

  // Form data automatically saves as user types
  // If they reload, form is restored!

  return (
    <form>
      <input
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
      />
      {/* More fields */}
    </form>
  );
}
```

### Example 3: Table Sort/Filter State

```tsx
function DataTable() {
  const [tableState, setTableState] = usePersistedState('dataTable', {
    sortBy: 'name',
    sortOrder: 'asc',
    page: 1,
    pageSize: 10,
    filters: {},
  });

  // User's table preferences persist!
  return <div>{/* Table component */}</div>;
}
```

## Best Practices

### ✅ DO:

- **Use meaningful keys** - `'dashboardFilters'` instead of `'data'`
- **Provide defaults** - Always provide a default value
- **Handle errors** - The utilities handle errors, but be aware
- **Clear when needed** - Clear storage on logout or form submission

### ❌ DON'T:

- **Store sensitive data** - No passwords, tokens should be minimal
- **Store large objects** - localStorage has size limits (5-10MB)
- **Store functions** - Can't serialize functions to JSON
- **Store non-serializable data** - Only JSON-serializable data

## Clearing Data

### Clear on Logout

```tsx
// In your logout function
import { clearStorage } from '../utils/storage';

function handleLogout() {
  // Clear all user-related data
  clearStorage('dashboard'); // Clear all keys starting with 'dashboard'
  clearStorage('form'); // Clear all keys starting with 'form'
  
  // Or clear specific keys
  removeFromStorage('dashboardFilters');
  removeFromStorage('eventForm');
  
  // Clear auth data
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('accountType');
}
```

### Clear on Form Submit

```tsx
async function handleSubmit() {
  try {
    await submitForm(formData);
    
    // Clear form data after successful submission
    removeFromStorage('eventForm');
    setFormData({});
  } catch (error) {
    // Keep form data if submission fails
  }
}
```

## Storage Keys Reference

Common storage keys used in your app:

- `token` - Authentication token
- `username` - Logged in username
- `accountType` - User account type (admin/officer/member)
- `membershipCache` - Member data cache
- `formData` - Current form data (from FormDataProvider)
- `accountDetails` - Account details (from AccountDetailsProvider)
- `recentProjectSearches` - Recent search history

## Testing

To test if persistence works:

1. Fill in a form or set filters
2. Reload the page (F5)
3. Data should still be there! ✅

## Troubleshooting

### Data not persisting?
- Check browser console for errors
- Verify localStorage is enabled (some browsers allow disabling it)
- Check if you're using the correct key name
- Make sure data is JSON-serializable

### Data persisting when it shouldn't?
- Clear storage on logout/submit
- Use `sessionStorage` instead for temporary data
- Set expiration times if needed

## Summary

- ✅ Use `usePersistedState` hook for simple state persistence
- ✅ Use `FormDataProvider` for form data (already enhanced)
- ✅ Use `AccountDetailsProvider` for user data (already enhanced)
- ✅ Use storage utilities for manual operations
- ✅ Use `useScrollRestoration` for scroll position
- ✅ Clear storage when appropriate (logout, form submit)

Your app now automatically persists important state after reloads! 🎉

