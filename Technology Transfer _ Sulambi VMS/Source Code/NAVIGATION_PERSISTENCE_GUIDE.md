# Navigation Persistence Guide - Keep Data When Switching Pages

This guide shows you how to make data persist when **navigating between pages** (not just on refresh).

## What's New

✅ **Page-specific persistence** - Each page gets its own storage  
✅ **Navigation-aware** - Data saves when navigating away, restores when coming back  
✅ **Per-route storage** - `/dashboard` has separate data from `/calendar`  
✅ **Enhanced FormDataProvider** - Now supports per-page form data  

## Three Ways to Use

### 1. Use `usePagePersistence` Hook (Recommended)

**Best for**: Page-specific filters, search, form data

```tsx
import { usePagePersistence } from '../hooks/usePagePersistence';

function DashboardPage() {
  // Filters persist when navigating away and coming back!
  const [filters, setFilters] = usePagePersistence('filters', {
    status: '',
    date: '',
    search: '',
  });

  return (
    <div>
      <input
        value={filters.search}
        onChange={(e) => setFilters({ ...filters, search: e.target.value })}
      />
      {/* Navigate to another page, then come back - filters are still there! ✅ */}
    </div>
  );
}
```

**Features**:
- ✅ Automatically saves when state changes
- ✅ Automatically restores when you return to the page
- ✅ Each page has separate storage (no conflicts)
- ✅ Works with any data type

### 2. Use Enhanced `FormDataProvider`

**Best for**: Forms that persist across navigation

The `FormDataProvider` now automatically saves form data per page:

```tsx
import { useContext } from 'react';
import { FormDataContext } from '../contexts/FormDataProvider';

function EventForm() {
  const { formData, setFormData } = useContext(FormDataContext);

  // Fill out the form
  // Navigate to another page
  // Come back - form data is still there! ✅

  return (
    <form>
      <input
        value={formData.title || ''}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
      />
    </form>
  );
}
```

**New methods available**:
```tsx
const { 
  formData,              // Current form data
  setFormData,           // Update form data
  getPageFormData,       // Get form data for specific page
  setPageFormData,       // Set form data for specific page
  resetFormData,         // Clear current page form data
} = useContext(FormDataContext);
```

### 3. Use `PageStateProvider` Context

**Best for**: Complex page state management

```tsx
import { useContext } from 'react';
import { PageStateContext } from '../contexts/PageStateProvider';

function MyPage() {
  const { getState, setState, clearState } = useContext(PageStateContext);

  // Save state
  const handleSave = () => {
    setState('myKey', { data: 'value' });
  };

  // Load state
  const myData = getState('myKey', { data: '' });

  // Clear state
  const handleClear = () => {
    clearState('myKey'); // Clear specific key
    clearState();        // Clear all state for this page
  };

  return <div>{/* Your component */}</div>;
}
```

## Examples

### Example 1: Dashboard Filters (Most Common)

```tsx
// src/pages/Admin/DashboardPage.tsx
import { usePagePersistence } from '../../../hooks/usePagePersistence';

function DashboardPage() {
  const [filters, setFilters] = usePagePersistence('dashboardFilters', {
    status: 'all',
    dateFrom: '',
    dateTo: '',
    searchQuery: '',
  });

  // Filters persist across navigation! ✅
  
  return (
    <div>
      <select
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
      >
        {/* Options */}
      </select>
      {/* More filter inputs */}
    </div>
  );
}
```

**What happens**:
1. User sets filters on `/admin/dashboard`
2. User navigates to `/admin/calendar`
3. User comes back to `/admin/dashboard`
4. **Filters are still there!** ✅

### Example 2: Form with Auto-Save

```tsx
// src/pages/Officer/EventProposal.tsx
import { usePagePersistence } from '../../../hooks/usePagePersistence';

function EventProposal() {
  const [formData, setFormData] = usePagePersistence('eventProposal', {
    title: '',
    description: '',
    date: '',
    location: '',
  });

  // User fills form, navigates away, comes back - data is still there! ✅

  return (
    <form>
      <input
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
      />
      {/* More form fields */}
    </form>
  );
}
```

### Example 3: Table State (Sort, Pagination, Filters)

```tsx
function DataTable() {
  const [tableState, setTableState] = usePagePersistence('dataTable', {
    sortBy: 'name',
    sortOrder: 'asc',
    page: 1,
    pageSize: 10,
    filters: {},
  });

  // Table preferences persist across navigation! ✅

  return (
    <table>
      {/* Table content */}
    </table>
  );
}
```

### Example 4: Search History Per Page

```tsx
function SearchPage() {
  const [recentSearches, setRecentSearches] = usePagePersistence('recentSearches', []);

  const handleSearch = (query: string) => {
    // Add to recent searches
    setRecentSearches([query, ...recentSearches].slice(0, 10));
  };

  // Recent searches persist per page! ✅
  
  return (
    <div>
      {recentSearches.map((search, i) => (
        <button key={i} onClick={() => handleSearch(search)}>
          {search}
        </button>
      ))}
    </div>
  );
}
```

### Example 5: Clear on Submit

```tsx
import { usePagePersistence, useClearPagePersistence } from '../hooks/usePagePersistence';

function EventForm() {
  const [formData, setFormData] = usePagePersistence('eventForm', {
    title: '',
    description: '',
  });
  
  const clearPageData = useClearPagePersistence();

  const handleSubmit = async () => {
    await submitForm(formData);
    
    // Clear form data after successful submission
    clearPageData('eventForm');
    setFormData({ title: '', description: '' });
  };

  return <form>{/* Form fields */}</form>;
}
```

## Advanced: Global State (Across All Pages)

For app-wide settings that should persist across all pages:

```tsx
import { useGlobalPersistence } from '../hooks/usePagePersistence';

function SettingsPage() {
  // These preferences work on ALL pages
  const [userPreferences, setUserPreferences] = useGlobalPersistence('userPrefs', {
    theme: 'light',
    language: 'en',
    notifications: true,
  });

  return <div>{/* Settings UI */}</div>;
}
```

## How It Works

### Storage Structure

```
localStorage:
  - formData: {...}                    // Global form data
  - pageFormData: {                    // Per-page form data
      "/admin/dashboard": {...},
      "/admin/calendar": {...},
    }
  - page_/admin/dashboard_filters: {...}  // Page-specific filters
  - page_/admin/calendar_filters: {...}   // Different page, different data
```

### Lifecycle

1. **User navigates to page** → Component mounts
2. **Hook loads data** → Reads from localStorage for this route
3. **User interacts** → Data updates, saves to localStorage
4. **User navigates away** → Component unmounts, data stays in localStorage
5. **User returns** → Component mounts, hook loads saved data
6. **Data restored** → User sees their previous data ✅

## Best Practices

### ✅ DO:

- **Use page-specific keys** - `'filters'` instead of `'data'`
- **Provide defaults** - Always provide a default value
- **Clear on submit** - Clear data after successful form submission
- **Use appropriate hooks** - `usePagePersistence` for page data, `useGlobalPersistence` for app-wide

### ❌ DON'T:

- **Store sensitive data** - No passwords or tokens
- **Store large objects** - Keep data small
- **Forget to clear** - Clear data when no longer needed
- **Mix page and global** - Be consistent about scope

## Testing

### Test Navigation Persistence:

1. **Go to a page** (e.g., `/admin/dashboard`)
2. **Set some filters** or fill a form
3. **Navigate to another page** (e.g., `/admin/calendar`)
4. **Navigate back** to the first page
5. **Data should still be there!** ✅

### Test Page Refresh:

1. **Set data on a page**
2. **Press F5** (refresh)
3. **Data should still be there!** ✅

## Integration with Existing Code

### Option 1: Gradual Migration

Start using `usePagePersistence` in new components, keep old code working:

```tsx
// Old way (still works)
const [filters, setFilters] = useState({ status: '' });

// New way (with persistence)
const [filters, setFilters] = usePagePersistence('filters', { status: '' });
```

### Option 2: Wrap App with PageStateProvider

Add to your `App.tsx`:

```tsx
import { PageStateProvider } from './contexts/PageStateProvider';

function App() {
  return (
    <BrowserRouter>
      <PageStateProvider>
        <Routes>
          {/* Your routes */}
        </Routes>
      </PageStateProvider>
    </BrowserRouter>
  );
}
```

## Troubleshooting

### Data not persisting?

- Check if you're using the correct hook
- Verify the storage key is correct
- Check browser console for errors
- Ensure localStorage is enabled

### Data persisting when it shouldn't?

- Use `clearPageData()` after form submission
- Use `clearOnUnmount` option for temporary data
- Clear on logout

### Different pages sharing data?

- Make sure storage keys are unique per page
- Check that you're using page-specific hooks
- Verify route paths are different

## Summary

✅ **Navigation persistence is now enabled!**

- Use `usePagePersistence` for page-specific data
- Use `FormDataProvider` for forms (auto-enhanced)
- Use `PageStateProvider` for complex state management
- Data persists when navigating away and coming back
- Data also persists on page refresh (F5)

**Your data now survives both navigation AND refresh!** 🎉

