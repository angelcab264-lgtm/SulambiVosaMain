/**
 * Get the correct path for public images
 * Works for both local development and production (Render)
 */
export const getImagePath = (imagePath: string): string => {
  // Remove leading slash if present to normalize
  const normalizedPath = imagePath.startsWith('/') ? imagePath.slice(1) : imagePath;
  
  // Use Vite's BASE_URL which is '/' in production
  // This ensures images work both locally and on Render
  const baseUrl = import.meta.env.BASE_URL || '/';
  
  // Ensure baseUrl ends with / and path doesn't start with /
  const base = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  const path = normalizedPath.startsWith('/') ? normalizedPath.slice(1) : normalizedPath;
  
  return `${base}${path}`;
};





