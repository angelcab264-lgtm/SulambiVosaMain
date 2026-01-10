import { createContext, ReactNode, useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { produce } from "immer";
import { saveToStorage, getFromStorage } from "../utils/storage";

interface Triplets {
  formData: any;
  setFormData: (value: any) => void;
  immutableSetFormData: (immutableVal: any) => void;
  mutableSetFormData: (mutableVal: any) => void;
  resetFormData: () => void;
  // New: Page-specific form data methods
  getPageFormData: (pagePath?: string) => any;
  setPageFormData: (pagePath: string, data: any) => void;
}

export const FormDataContext = createContext<Triplets>({
  formData: {},
  setFormData: () => {},
  immutableSetFormData: () => {},
  mutableSetFormData: () => {},
  resetFormData: () => {},
  getPageFormData: () => ({}),
  setPageFormData: () => {},
});

const FormDataProvider = ({ children }: { children: ReactNode }) => {
  const location = useLocation();
  
  // Global form data (for backward compatibility)
  const [formData, setFormData] = useState(() => {
    try {
      const saved = getFromStorage('formData', {});
      return saved || {};
    } catch (error) {
      console.error('Error loading form data from storage:', error);
      return {};
    }
  });

  // Page-specific form data (persists per route)
  const [pageFormData, setPageFormData] = useState<Record<string, any>>(() => {
    try {
      const saved = getFromStorage('pageFormData', {});
      return saved || {};
    } catch (error) {
      console.error('Error loading page form data from storage:', error);
      return {};
    }
  });

  // Load form data for current page when navigating
  useEffect(() => {
    try {
      const pageData = pageFormData[location.pathname];
      if (pageData) {
        // Merge page-specific data with global data
        setFormData((prev) => ({ ...prev, ...pageData }));
      }
    } catch (error) {
      console.error('Error loading page form data:', error);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Save global form data to localStorage whenever it changes
  useEffect(() => {
    try {
      if (Object.keys(formData).length > 0) {
        saveToStorage('formData', formData);
        // Also save to current page's form data
        const updated = {
          ...pageFormData,
          [location.pathname]: formData,
        };
        setPageFormData(updated);
        saveToStorage('pageFormData', updated);
      }
    } catch (error) {
      console.error('Error saving form data to storage:', error);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData]);

  const immutableSetFormData = (immutableVal: any) => {
    setFormData((prevData) =>
      produce(prevData, (draft) => {
        Object.assign(draft, immutableVal);
      })
    );
  };

  const mutableSetFormData = (immutableVal: any) => {
    setFormData((prevData) => ({ ...prevData, ...immutableVal }));
  };

  const resetFormData = () => {
    setFormData({});
    // Also clear current page's form data
    const updated = { ...pageFormData };
    delete updated[location.pathname];
    setPageFormData(updated);
    saveToStorage('pageFormData', updated);
  };

  const getPageFormData = (pagePath?: string) => {
    const path = pagePath || location.pathname;
    return pageFormData[path] || {};
  };

  const setPageFormDataForPath = (pagePath: string, data: any) => {
    const updated = {
      ...pageFormData,
      [pagePath]: data,
    };
    setPageFormData(updated);
    saveToStorage('pageFormData', updated);
    
    // If it's the current page, also update global formData
    if (pagePath === location.pathname) {
      setFormData(data);
    }
  };

  return (
    <FormDataContext.Provider
      value={{
        formData,
        setFormData,
        immutableSetFormData,
        mutableSetFormData,
        resetFormData,
        getPageFormData,
        setPageFormData: setPageFormDataForPath,
      }}
    >
      {children}
    </FormDataContext.Provider>
  );
};

export default FormDataProvider;
