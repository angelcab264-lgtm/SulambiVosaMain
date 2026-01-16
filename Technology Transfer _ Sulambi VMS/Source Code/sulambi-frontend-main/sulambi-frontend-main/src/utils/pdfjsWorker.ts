/**
 * PDF.js Worker Configuration
 * This file must be imported BEFORE any react-pdf components are used
 * to ensure the worker is configured correctly
 */

import { pdfjs } from "react-pdf";

// Set up PDF.js worker with reliable CDN
// react-pdf 9.1.1 uses PDF.js 4.8.69
const pdfjsVersion = pdfjs.version || "4.8.69";

// Use unpkg.com which is more reliable than cdnjs
// Force set to unpkg to avoid cdnjs 404 errors
const workerUrl = `https://unpkg.com/pdfjs-dist@${pdfjsVersion}/build/pdf.worker.min.js`;

// Override any default worker source
pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

// Log for debugging
console.log(`[PDFJS_WORKER] Configured worker: ${workerUrl}`);
console.log(`[PDFJS_WORKER] PDF.js version: ${pdfjsVersion}`);

export default pdfjs;

