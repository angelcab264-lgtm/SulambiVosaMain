import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { Box, IconButton, Typography, CircularProgress, Alert } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import DownloadIcon from "@mui/icons-material/Download";
import NavigateBeforeIcon from "@mui/icons-material/NavigateBefore";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface Props {
  url: string;
  open: boolean;
  setOpen?: (state: boolean) => void;
}

const LocalPDFViewer: React.FC<Props> = ({ url, open, setOpen }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !url) return;

    const fetchPdfData = async () => {
      setLoading(true);
      setError(null);
      setPageNumber(1);
      setPdfUrl(null);

      try {
        // Get authentication token
        const token = localStorage.getItem("token");
        const headers: HeadersInit = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        // Fetch PDF with authentication
        const response = await fetch(url, {
          headers,
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error(`Failed to load PDF: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        setPdfUrl(objectUrl);
      } catch (err: any) {
        console.error("Error loading PDF:", err);
        setError(err.message || "Failed to load PDF. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchPdfData();

    // Cleanup object URL on unmount
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [url, open]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const onDocumentLoadError = (error: Error) => {
    console.error("PDF load error:", error);
    setError("Failed to parse PDF. The file may be corrupted.");
    setLoading(false);
  };

  const goToPrevPage = () => {
    if (pageNumber > 1) {
      setPageNumber(pageNumber - 1);
    }
  };

  const goToNextPage = () => {
    if (numPages && pageNumber < numPages) {
      setPageNumber(pageNumber + 1);
    }
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleDownload = () => {
    if (pdfUrl) {
      const link = document.createElement("a");
      link.href = pdfUrl;
      link.download = url.split("/").pop() || "document.pdf";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  if (!open) return null;

  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.9)",
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Header with controls */}
      <Box
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          backgroundColor: "rgba(0, 0, 0, 0.8)",
          padding: "10px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          zIndex: 10000,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <IconButton
            onClick={handleZoomOut}
            sx={{ color: "white" }}
            disabled={scale <= 0.5}
          >
            <ZoomOutIcon />
          </IconButton>
          <Typography sx={{ color: "white", minWidth: "60px", textAlign: "center" }}>
            {Math.round(scale * 100)}%
          </Typography>
          <IconButton
            onClick={handleZoomIn}
            sx={{ color: "white" }}
            disabled={scale >= 3}
          >
            <ZoomInIcon />
          </IconButton>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <IconButton
            onClick={goToPrevPage}
            sx={{ color: "white" }}
            disabled={pageNumber <= 1}
          >
            <NavigateBeforeIcon />
          </IconButton>
          <Typography sx={{ color: "white", minWidth: "100px", textAlign: "center" }}>
            Page {pageNumber} of {numPages || "?"}
          </Typography>
          <IconButton
            onClick={goToNextPage}
            sx={{ color: "white" }}
            disabled={!numPages || pageNumber >= numPages}
          >
            <NavigateNextIcon />
          </IconButton>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <IconButton onClick={handleDownload} sx={{ color: "white" }} title="Download PDF">
            <DownloadIcon />
          </IconButton>
          <IconButton
            onClick={() => setOpen && setOpen(false)}
            sx={{ color: "white" }}
            title="Close"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </Box>

      {/* PDF Content */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "100%",
          padding: "60px 20px 20px",
          overflow: "auto",
        }}
      >
        {loading && (
          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
            <CircularProgress sx={{ color: "white" }} />
            <Typography sx={{ color: "white" }}>Loading PDF...</Typography>
          </Box>
        )}

        {error && (
          <Alert 
            severity="error" 
            sx={{ maxWidth: "500px" }}
            action={
              <IconButton
                color="inherit"
                size="small"
                onClick={() => {
                  // Fallback: open PDF in new tab
                  if (url) {
                    window.open(url, "_blank");
                  }
                }}
              >
                <DownloadIcon />
              </IconButton>
            }
          >
            {error}
            <br />
            <Typography variant="caption">
              If this is a protected file, make sure you're logged in.
              <br />
              Click the download icon to try opening in a new tab.
            </Typography>
          </Alert>
        )}

        {pdfUrl && !loading && !error && (
          <Box
            sx={{
              backgroundColor: "white",
              padding: "20px",
              borderRadius: "4px",
              boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            }}
          >
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <Box sx={{ display: "flex", justifyContent: "center", padding: "40px" }}>
                  <CircularProgress />
                </Box>
              }
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default LocalPDFViewer;
