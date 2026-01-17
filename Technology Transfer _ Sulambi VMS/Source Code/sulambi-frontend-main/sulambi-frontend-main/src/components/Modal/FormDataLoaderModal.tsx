import React, { ReactNode, useEffect, useState } from "react";
import PopupModal from "./PopupModal";
import ExternalEventForm from "../TemplateForms/TemplateForms/ExternalEventForm";
import EvaluationForm from "../TemplateForms/TemplateForms/EvaluationForm";
import { Box } from "@mui/material";
import FlexBox from "../FlexBox";
import PrimaryButton from "../Buttons/PrimaryButton";
import LocalPrintshopIcon from "@mui/icons-material/LocalPrintshop";
import InternalEventForm from "../TemplateForms/TemplateForms/InternalEventForm";
import { createRoot } from "react-dom/client";
import ExternalReport from "../TemplateForms/TemplateForms/ExternalReport";
import InternalReport from "../TemplateForms/TemplateForms/InternalReport";
import { getEventDetails } from "../../api/dashboard";
import { getSignatory } from "../../api/events";
import {
  applyExternalReportPrintFix,
  cleanupExternalReportPrintFix,
} from "../../utils/externalReportPrintFix";

interface Props {
  data: any;
  open: boolean;
  formType:
    | "externalEvent"
    | "internalEvent"
    | "evaluation"
    | "externalReport"
    | "internalReport";
  textAlign?: "left" | "justify";
  hidePrintButton?: boolean;
  beforePrintComponent?: ReactNode;
  setOpen?: (state: boolean) => void;
}

const FormDataLoaderModal: React.FC<Props> = ({
  formType,
  textAlign,
  data,
  open,
  hidePrintButton,
  beforePrintComponent,
  setOpen,
}) => {
  const [formTemplate, setFormTemplate] = useState<React.ReactNode>(<></>);

  const printForm = () => {
    let printRoot: any = null;
    let printContainer: HTMLDivElement | null = null;

    // Create print container
    printContainer = document.createElement("div");
    printContainer.id = "print-container-temp";
    printContainer.style.width = "100%";
    // render offscreen initially so React can render
    printContainer.style.position = "absolute";
    printContainer.style.left = "-9999px";
    printContainer.style.top = "0";
    document.body.appendChild(printContainer);

    // EARLY PRINT STYLE: Inject before React renders to ensure rules exist during DOM creation
    const earlyPrintStyle = document.createElement('style');
    earlyPrintStyle.id = 'print-early-fallbacks';
    earlyPrintStyle.textContent = `
      @media print {
        /* make sure the print container prints as expected */
      #print-container-temp, #print-container-temp * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
        visibility: visible !important;
        opacity: 1 !important;
      }

        /* Light outer box: use outline only (1px) for crisp single line, NO box-shadow to avoid dark/thick look */
        #print-container-temp table.bsuFormChild,
        #print-container-temp .page-box {
          border-collapse: collapse !important;
          border-spacing: 0 !important;
          border: 0 none !important;
          outline: 0.5px solid #666 !important;                 /* lighter border line, visible on each printed page */
          box-shadow: none !important;                        /* remove box-shadow to prevent dark/thick appearance */
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }
        
        /* Remove outline from first content table to avoid dark overlap with signatories table */
        #print-container-temp .header-content-group > table.bsuFormChild:first-of-type,
        #print-container-temp .header-content-group > table.bsuForm + table.bsuFormChild {
          outline: none !important;
        }
        
        /* Remove outline (box border) from eval-compact tables - keep only cell borders */
        #print-container-temp table.bsuFormChild.eval-compact,
        #print-container-temp table.bsuFormChild.compact.eval-compact {
          outline: none !important;
        }

        /* CRITICAL: Force ALL borders on ALL cells - including continuation on new pages */
        /* When a cell's content continues to another page, the continuation MUST have full borders */
        /* EXCEPT for eval-compact tables which have their own rules */
        #print-container-temp table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) td,
        #print-container-temp table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) th {
          /* Primary border method - force all sides - lighter borders */
          border: 0.5px solid #666 !important;
          border-top: 0.5px solid #666 !important;
          border-bottom: 0.5px solid #666 !important;
          border-left: 0.5px solid #666 !important;
          border-right: 0.5px solid #666 !important;
          border-style: solid !important;
          border-width: 0.5px !important;
          border-color: #666 !important;
          padding: 4px 6px !important;
          font-size: 10pt !important;
          background-clip: padding-box !important;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
          /* CRITICAL: Use box-decoration-break to clone borders on page breaks */
          box-decoration-break: clone !important;
          -webkit-box-decoration-break: clone !important;
          /* CRITICAL: Use outline as backup border method for page breaks - lighter borders */
          /* Outline appears on continuation pages even when border doesn't */
          outline: 0.5px solid #666 !important;
          outline-offset: -0.5px !important;
        }

        /* CRITICAL: Force borders on ALL cells - no exceptions - lighter borders */
        /* This ensures continuation pages always have borders */
        /* EXCEPT for eval-compact tables which have their own rules */
        #print-container-temp table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) tbody tr td,
        #print-container-temp table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) tbody tr th,
        #print-container-temp table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) thead tr th {
          border-top: 0.5px solid #666 !important;
          border-bottom: 0.5px solid #666 !important;
          border-left: 0.5px solid #666 !important;
          border-right: 0.5px solid #666 !important;
          outline: 0.5px solid #666 !important;
          outline-offset: -0.5px !important;
        }

        /* Allow rows to break but avoid large groups being kept incorrectly */
        #print-container-temp table.bsuFormChild {
          page-break-inside: auto !important;
          break-inside: auto !important;
          orphans: 1 !important;
          widows: 1 !important;
        }
        #print-container-temp table.bsuFormChild > tbody > tr {
          page-break-inside: avoid !important; /* try to keep a row whole */
          break-inside: avoid !important;
        }

        /* debug helper: make the print-box very visible for troubleshooting (remove in final) */
        /* #print-container-temp { outline: 3px dashed magenta !important; } */
      }
    `;
    document.head.appendChild(earlyPrintStyle);

    // Render the formTemplate into print container
    printRoot = createRoot(printContainer);
    printRoot.render(formTemplate);

    const preparePrint = () => {
      if (!printContainer) return;
      const readyStart = Date.now();
      const MAX_READY_WAIT_MS = 2500; // don't block print forever if images are slow
        
      // Wait for images and other resources to load
      const checkReady = () => {
        const images = printContainer?.querySelectorAll("img");
        let imagesLoaded = true;
        if (images && images.length > 0) {
          images.forEach((img) => {
            if (!(img as HTMLImageElement).complete) {
              imagesLoaded = false;
            }
          });
        }
        if (!imagesLoaded) {
          // If some images are slow/hung, proceed anyway after a short timeout
          if (Date.now() - readyStart > MAX_READY_WAIT_MS) {
            console.warn("Print: proceeding without waiting for all images (timeout).");
            // Hide any images that still aren't loaded to avoid browser decode/paint stalls during print
            try {
              images?.forEach((img) => {
                const htmlImg = img as HTMLImageElement;
                // Hint to browser: decode asynchronously
                (htmlImg as any).decoding = "async";
                if (!htmlImg.complete) {
                  htmlImg.style.setProperty("display", "none", "important");
                }
              });
            } catch {
              // ignore
            }
          } else {
            setTimeout(checkReady, 100);
            return;
          }
        }

        // Move container to visible position for print
        if (printContainer) {
          printContainer.style.position = "static";
          printContainer.style.left = "auto";
          printContainer.style.top = "auto";
        }

        // Apply external report print fix if this is an external report
        let printFixCleanup: (() => void) | undefined;
        try {
          if (formType === "externalReport" && printContainer) {
            printFixCleanup = applyExternalReportPrintFix(printContainer);
          }
        } catch (error) {
          console.error("Error applying external report print fix:", error);
          // Continue with print even if fix fails
      }
      
      // Force layout recalculation
        void printContainer?.offsetHeight;
      
        // Add print styles that preserve exact ISO form format - match preview exactly
        // Override global print CSS to preserve component styles
      const style = document.createElement("style");
      style.id = "print-hide-style";
      style.textContent = `
          @page {
            margin-top: 0.6in;
            margin-bottom: 0.7in;
            margin-left: 0.7in;
            margin-right: 0.8in;
            size: letter;
            @bottom-right {
              content: "Page " counter(page);
              font-family: "Times New Roman", Times, serif;
              font-size: 10pt;
              color: black;
            }
          }
          
          @page:first {
            margin-top: 0.6in;
            margin-bottom: 0.7in;
            margin-left: 0.7in;
            margin-right: 0.8in;
            @bottom-left {
              content: "Tracking No. : ___________";
              font-family: "Times New Roman", Times, serif;
              font-size: 10pt;
              color: black;
            }
            @bottom-right {
              content: "Page " counter(page);
              font-family: "Times New Roman", Times, serif;
              font-size: 10pt;
              color: black;
            }
          }
          
          @media print {
            /* Hide browser default headers and footers */
            
            /* Hide everything except print container */
            body > *:not(#print-container-temp) {
              display: none !important;
            }
            
            /* Print container - preserve exact preview appearance */
              #print-container-temp {
              display: block !important;
              position: static !important;
              margin: 0 !important;
                padding: 0 !important;
              width: 100% !important;
              background: white !important;
            }
            
            /* CRITICAL: Ensure content starts on first page - no page break before */
            #print-container-temp,
            #print-container-temp > *:first-child,
            #print-container-temp .bsu-form-wrapper:first-child,
            #print-container-temp .header-content-group:first-child {
              page-break-before: auto !important;
              break-before: auto !important;
              margin-top: 0 !important;
              padding-top: 0 !important;
            }
            
            /* CRITICAL: Override global print CSS to match preview exactly */
            /* Restore preview appearance by overriding aggressive print rules from index.css */
            
            /* Preserve bsu-form-wrapper as in preview */
            #print-container-temp .bsu-form-wrapper {
              gap: 0 !important;
              row-gap: 0 !important;
              display: flex !important;
              flex-direction: column !important;
              align-items: stretch !important;
              margin: 0 !important;
              padding: 0 !important;
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            /* Remove any spacing between direct children of bsu-form-wrapper */
            #print-container-temp .bsu-form-wrapper > * {
              margin-top: 0 !important;
              margin-bottom: 0 !important;
            }
            
            /* First child (header table) should have no bottom margin */
            #print-container-temp .bsu-form-wrapper > *:first-child {
              margin-bottom: 0 !important;
            }
            
            /* Second child (first content table) should have no top margin */
            #print-container-temp .bsu-form-wrapper > *:nth-child(2) {
              margin-top: 0 !important;
            }
            
            /* CRITICAL: Keep header and first content together on first page */
            /* Match the image layout where header and content appear on same page */
            #print-container-temp .header-content-group {
              page-break-inside: auto !important;
              break-inside: auto !important;
              margin: 0 !important;
              padding: 0 !important;
              display: block !important;
              gap: 0 !important;
              row-gap: 0 !important;
            }
            
            /* Keep first few tables together on first page */
            #print-container-temp .bsu-form-wrapper {
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            /* Specifically keep header + first 2-3 content tables together */
            #print-container-temp .bsu-form-wrapper > table.bsuForm:first-child,
            #print-container-temp .bsu-form-wrapper > table.bsuFormChild:nth-child(2),
            #print-container-temp .bsu-form-wrapper > table.bsuFormChild:nth-child(3) {
              page-break-after: auto !important;
              break-after: auto !important;
            }
            
            /* Remove any spacing from children of header-content-group */
            #print-container-temp .header-content-group > * {
              margin-top: 0 !important;
              margin-bottom: 0 !important;
              padding-top: 0 !important;
              padding-bottom: 0 !important;
            }
            
            /* Specifically target the first child (header table) and second child (first content table) */
            #print-container-temp .header-content-group > *:first-child {
              margin-bottom: 0 !important;
              padding-bottom: 0 !important;
            }
            
            #print-container-temp .header-content-group > *:nth-child(2) {
              margin-top: 0 !important;
              padding-top: 0 !important;
            }
            
            /* Header table - no page break after, keep with first content */
            #print-container-temp .header-content-group > table.bsuForm,
            #print-container-temp .bsu-form-wrapper > table.bsuForm:first-child {
              page-break-after: auto !important;
              break-after: auto !important;
              margin-top: 0 !important;
              margin-bottom: 0 !important;
              padding-bottom: 0 !important;
            }
            
            /* First content table - no page break before, stay with header on first page */
            /* CRITICAL: First content table must have ZERO margins to connect seamlessly with header */
            #print-container-temp .header-content-group > table.bsuFormChild:first-of-type,
            #print-container-temp .header-content-group > table.bsuForm + table.bsuFormChild,
            #print-container-temp .bsu-form-wrapper > table.bsuForm + table.bsuFormChild {
              page-break-before: auto !important;
              break-before: auto !important;
              margin-top: 0 !important;
              margin-bottom: 0 !important;
              padding-top: 0 !important;
              padding-bottom: 0 !important;
            }
            
            /* Preserve header table margins - no top margin to start at top of page */
            #print-container-temp .bsu-form-wrapper > table.bsuForm:first-child {
              margin-top: 0 !important;
              margin-bottom: 0 !important;
            }
            
            #print-container-temp .bsu-form-wrapper > table.bsuForm {
              margin-bottom: 0 !important;
            }
            
            /* Ensure header table and first content table connect seamlessly - NO GAP */
            /* Remove bottom border from header table (signatories) when followed by content table */
            #print-container-temp .header-content-group > table.bsuForm {
              border-bottom: none !important;
              margin-bottom: 0 !important;
              padding-bottom: 0 !important;
            }
            
            /* Remove top outline/border from first content table to avoid dark double-line with signatories */
            #print-container-temp .header-content-group > table.bsuFormChild:first-of-type,
            #print-container-temp .header-content-group > table.bsuForm + table.bsuFormChild,
            #print-container-temp .bsu-form-wrapper > table.bsuForm + table.bsuFormChild {
              border-top: none !important;
              outline: none !important;  /* Remove outline to prevent dark overlap with signatories table */
              margin-top: 0 !important;
              margin-bottom: 0 !important;
              padding-top: 0 !important;
            }
            
            /* Override global print CSS that removes margins - restore preview margins */
            /* This overrides the @media print rule in index.css that sets margin: 0 !important */
            /* Default: All tables have no margins - we'll add spacing only where needed */
            #print-container-temp table.bsuFormChild {
              font-size: 10pt !important;
              border: 0.5px solid #666 !important; /* Lighter border */
              /* REMOVED: border-top: none - Layer 3 needs top borders for continuation pages */
              border-collapse: collapse !important;
              width: 100% !important;
              max-width: none !important;
              table-layout: fixed !important;
              text-wrap: wrap !important;
              word-wrap: break-word !important;
              overflow-wrap: break-word !important;
              margin: 0 !important;
              margin-top: 0 !important;
              margin-bottom: 0 !important;
            }
            
            /* CRITICAL: First content table (right after header) must have ZERO margins */
            #print-container-temp .header-content-group > table.bsuFormChild:first-of-type,
            #print-container-temp .header-content-group > table.bsuForm + table.bsuFormChild,
            #print-container-temp .bsu-form-wrapper > table.bsuForm + table.bsuFormChild:first-of-type {
              margin: 0 !important;
              margin-top: 0 !important;
              margin-bottom: 0 !important;
            }
            
            /* CRITICAL: Remove spacing between consecutive bsuFormChild tables */
            /* This eliminates the large space between checkbox table and content table */
            #print-container-temp table.bsuFormChild + table.bsuFormChild {
              margin-top: 0 !important;
              margin-bottom: 0 !important;
              padding-top: 0 !important;
              padding-bottom: 0 !important;
            }
            
            /* Remove bottom margin from any table that is followed by another table */
            /* This ensures no gap between consecutive tables */
            #print-container-temp .bsu-form-wrapper > table.bsuFormChild:has(+ table.bsuFormChild),
            #print-container-temp .header-content-group > table.bsuFormChild:has(+ table.bsuFormChild) {
              margin-bottom: 0 !important;
            }
            
            /* Fallback for browsers that don't support :has() - use adjacent sibling */
            #print-container-temp table.bsuFormChild:not(:last-child) {
              margin-bottom: 0 !important;
            }
            
            /* Only the last table in a group gets bottom margin for section spacing */
            #print-container-temp .bsu-form-wrapper > table.bsuFormChild:last-child,
            #print-container-temp .header-content-group > table.bsuFormChild:last-child {
              margin-bottom: 10px !important;
            }
            
            /* CRITICAL: Cell borders - ensure ALL cells have FULL borders on continuation pages */
            /* When a cell's content continues to another page, the continuation MUST have borders on ALL sides */
            #print-container-temp table.bsuFormChild > tbody > tr > td,
            #print-container-temp table.bsuFormChild > thead > tr > th,
            #print-container-temp table.bsuFormChild > tbody > tr > th {
              padding: 4px 6px !important;
              font-size: 10pt !important;
              
              /* PRIMARY: Standard borders on all sides - lighter borders */
              border: 0.5px solid #666 !important;
              border-top: 0.5px solid #666 !important;
              border-bottom: 0.5px solid #666 !important;
              border-left: 0.5px solid #666 !important;
              border-right: 0.5px solid #666 !important;
              border-style: solid !important;
              border-width: 0.5px !important;
              border-color: #666 !important;
              
              /* CRITICAL: Use outline as backup border method for page breaks - lighter borders */
              /* Outline is more reliable on continuation pages when cells break across pages */
              outline: 0.5px solid #666 !important;
              outline-offset: -1px !important;
              outline-style: solid !important;
              outline-width: 1px !important;
              outline-color: black !important;
              
              /* Force borders to appear even when cells break across pages */
              box-decoration-break: clone !important;
              -webkit-box-decoration-break: clone !important;
              
              /* Ensure borders are always visible on page breaks */
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
            }

            /* CRITICAL: Force borders on ALL cells - no exceptions for continuation pages */
            /* This ensures that when content continues to a new page, it has full borders - lighter borders */
            #print-container-temp table.bsuFormChild > tbody > tr > td,
            #print-container-temp table.bsuFormChild > tbody > tr > th {
              /* Force ALL borders explicitly */
              border-top: 0.5px solid #666 !important;
              border-bottom: 0.5px solid #666 !important;
              border-left: 0.5px solid #666 !important;
              border-right: 0.5px solid #666 !important;
              /* Backup outline borders for page breaks */
              outline: 0.5px solid #666 !important;
              outline-offset: -1px !important;
            }

            /* Ensure table uses border-collapse to maintain borders across page breaks */
            #print-container-temp table.bsuFormChild {
              border-collapse: collapse !important;
              border-spacing: 0 !important;
            }
            
            /* CRITICAL: OVERRIDE page-break-inside: avoid from index.css - ALLOW ROWS TO BREAK ACROSS PAGES */
            /* Must override the rule at index.css line 267 that prevents breaking */
            #print-container-temp table.bsuFormChild {
              page-break-inside: auto !important;
              break-inside: auto !important;
              orphans: 1 !important;
              widows: 1 !important;
            }
            
            #print-container-temp table.bsuFormChild > tbody {
              page-break-inside: auto !important;
              break-inside: auto !important;
              display: table-row-group !important;
              orphans: 1 !important;
              widows: 1 !important;
            }
            
            #print-container-temp table.bsuFormChild > tbody > tr {
              page-break-inside: auto !important;
              break-inside: auto !important;
              orphans: 1 !important;
              widows: 1 !important;
            }
            
            #print-container-temp table.bsuFormChild > tbody > tr > td,
            #print-container-temp table.bsuFormChild > tbody > tr > th,
            #print-container-temp table.bsuFormChild > thead > tr > th {
              page-break-inside: auto !important;
              break-inside: auto !important;
              orphans: 1 !important;
              widows: 1 !important;
            }
            
            /* Reduce padding in header table to save space */
            #print-container-temp table.bsuForm > tbody > tr > td,
            #print-container-temp table.bsuForm > thead > tr > th {
              padding: 3px 5px !important;
            }
            
            /* Preserve header-content-group as in preview */
            #print-container-temp .header-content-group {
              display: block !important;
              margin: 0 !important;
              padding: 0 !important;
              gap: 0 !important;
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            /* Ensure header table doesn't force a page break */
            #print-container-temp .header-content-group > table.bsuForm {
              page-break-after: auto !important;
              break-after: auto !important;
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            /* Ensure first content table stays with header on first page */
            #print-container-temp .header-content-group > table.bsuFormChild:first-of-type,
            #print-container-temp .header-content-group > table.bsuForm + table.bsuFormChild {
              page-break-before: auto !important;
              break-before: auto !important;
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            /* Preserve fontSet styling as in preview */
            #print-container-temp .fontSet {
              font-family: "Times New Roman", Times, serif !important;
              font-size: 10pt !important;
            }
            
            /* Ultra thin borders for Financial Plan and Evaluation Mechanics tables */
            /* Ultra thin black borders for Financial Plan and Evaluation Mechanics tables */
            /* CRITICAL: These rules must override the general bsuFormChild rules above */
            #print-container-temp table.financial-plan,
            #print-container-temp table.eval-compact,
            #print-container-temp table.bsuFormChild.eval-compact,
            #print-container-temp table.bsuFormChild.compact.eval-compact {
              border: 0.5px solid #000 !important;
              outline: none !important;
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
            }
            
            /* CRITICAL: Override ALL bsuFormChild border rules for eval-compact tables */
            #print-container-temp table.financial-plan th,
            #print-container-temp table.financial-plan td,
            #print-container-temp table.eval-compact th,
            #print-container-temp table.eval-compact td,
            #print-container-temp table.bsuFormChild.eval-compact td,
            #print-container-temp table.bsuFormChild.eval-compact th,
            #print-container-temp table.bsuFormChild.compact.eval-compact td,
            #print-container-temp table.bsuFormChild.compact.eval-compact th,
            #print-container-temp table.bsuFormChild.eval-compact > thead > tr > th,
            #print-container-temp table.bsuFormChild.eval-compact > tbody > tr > td,
            #print-container-temp table.bsuFormChild.compact.eval-compact > thead > tr > th,
            #print-container-temp table.bsuFormChild.compact.eval-compact > tbody > tr > td,
            #print-container-temp table.bsuFormChild.eval-compact tbody tr td,
            #print-container-temp table.bsuFormChild.eval-compact tbody tr th,
            #print-container-temp table.bsuFormChild.eval-compact thead tr th,
            #print-container-temp table.bsuFormChild.compact.eval-compact tbody tr td,
            #print-container-temp table.bsuFormChild.compact.eval-compact tbody tr th,
            #print-container-temp table.bsuFormChild.compact.eval-compact thead tr th,
            #print-container-temp table.bsuFormChild.eval-compact.internal-event-table-with-top-border > thead > tr > th,
            #print-container-temp table.bsuFormChild.eval-compact.internal-event-table-with-top-border > tbody > tr > td {
              border: 0.5px solid #000 !important;
              border-top: 0.5px solid #000 !important;
              border-bottom: 0.5px solid #000 !important;
              border-left: 0.5px solid #000 !important;
              border-right: 0.5px solid #000 !important;
              border-style: solid !important;
              border-width: 0.5px !important;
              border-color: #000 !important;
              outline: none !important;
              outline-offset: 0 !important;
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
              box-decoration-break: clone !important;
              -webkit-box-decoration-break: clone !important;
            }
            
            #print-container-temp table.financial-plan.internal-event-table-with-top-border,
            #print-container-temp table.eval-compact.internal-event-table-with-top-border,
            #print-container-temp table.bsuFormChild.eval-compact.internal-event-table-with-top-border {
              border-top: 0.5px solid #000 !important;
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
            }
            
            /* Centered table with equal spacing on both sides for Evaluation Mechanics table */
            #print-container-temp table.eval-compact {
              margin-left: auto !important;
              margin-right: auto !important;
              width: 90% !important;
              max-width: 90% !important;
            }
            
            /* Preserve RomanListValues spacing as in preview */
            #print-container-temp .roman-list-item {
              margin: 10px 0px !important;
              line-height: 1.5 !important;
              padding-left: 2.3em !important; /* Adjusted to match component spacing */
            }
            
            /* Adjust Roman numeral positioning in print */
            #print-container-temp .roman-list-item > span[aria-hidden="true"] {
              left: 0 !important;
              width: 2.3em !important;
            }
            
            /* Adjust content margin in print */
            #print-container-temp .roman-list-item > div > div {
              margin-left: 0.1em !important;
              padding-right: 8px !important; /* Reduced padding to move content slightly to the right */
            }
            
            /* Add left margin to Roman numeral sections container for better spacing */
            /* This targets the parent div of roman-list-item elements */
            #print-container-temp .fontSet[style*="marginLeft"] {
              margin-left: 50px !important; /* Increased from 40px to move content slightly to the right */
              margin-right: 10px !important;
            }
            
            /* Ensure color printing */
            #print-container-temp * {
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
            }
            
            /* Ensure all content is visible */
            #print-container-temp * {
              visibility: visible !important;
              opacity: 1 !important;
            }
            
            /* Ensure images print */
            #print-container-temp img {
              max-width: 100% !important;
              height: auto !important;
            }
            
            /* Internal Event Form: force page 2 to start at the marker so page-1 footer text stays on page 1 */
            #print-container-temp .internal-event-page-break {
              page-break-before: always !important;
              break-before: page !important;
            }
            
            /* Force page break for External Event Form Monitoring & Evaluation */
            #print-container-temp .external-event-page-break {
              page-break-before: always !important;
              break-before: page !important;
            }
            
            /* External Event Form - ensure main content starts on page 1 */
            #print-container-temp table.bsuFormChild.external-event-main-content {
              page-break-before: auto !important;
              break-before: auto !important;
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            #print-container-temp table.bsuFormChild.external-event-main-content > tbody > tr > td {
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
            
            /* Override the page-break-inside: avoid rule for External Event Form content cell */
            #print-container-temp table.bsuFormChild.external-event-main-content > tbody > tr:last-child > td {
              page-break-inside: auto !important;
              break-inside: auto !important;
            }
          }
          
          @media screen {
            #print-container-temp {
              position: fixed !important;
              top: 0 !important;
              left: 0 !important;
              width: 100% !important;
              height: 100% !important;
              background: white !important;
              z-index: 99999 !important;
              overflow: auto !important;
            }
        }
      `;
      document.head.appendChild(style);

      // Add a small UI control so the user can exit the print overlay if the browser fails to fire afterprint.
      const uiStyle = document.createElement("style");
      uiStyle.id = "print-ui-controls";
      uiStyle.textContent = `
        @media print {
          .print-exit-button { display: none !important; }
        }
        @media screen {
          .print-exit-button {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 1000000 !important;
            padding: 8px 12px !important;
            border-radius: 8px !important;
            border: 1px solid #999 !important;
            background: #fff !important;
            color: #111 !important;
            font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
            font-size: 12px !important;
            cursor: pointer !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
          }
        }
      `;
      document.head.appendChild(uiStyle);

      // After printing, restore and clean up
      const cleanup = () => {
          // Cleanup external report print fix
          if (printFixCleanup) {
            printFixCleanup();
          }
          cleanupExternalReportPrintFix(printContainer);

        if (printContainer && printContainer.parentNode) {
          printContainer.parentNode.removeChild(printContainer);
        }
        if (printRoot) {
          printRoot.unmount();
        }
        const hideStyle = document.getElementById("print-hide-style");
        if (hideStyle) {
          hideStyle.remove();
        }
        const earlyStyle = document.getElementById("print-early-fallbacks");
        if (earlyStyle) {
          earlyStyle.remove();
        }
        // Remove dynamic footer elements (if present)
        try {
          document.querySelectorAll("#footer-page-style").forEach((el) => el.remove());
          document.querySelectorAll("#print-container-temp .print-footer, #print-container-temp .print-footer-left, #print-container-temp .print-footer-right").forEach((el) => el.remove());
          document.querySelectorAll("#print-container-temp .print-margin-footer-left, #print-container-temp .print-margin-footer-right").forEach((el) => el.remove());
        } catch {
          // ignore
        }
        const controlsStyle = document.getElementById("print-ui-controls");
        if (controlsStyle) {
          controlsStyle.remove();
        }
        };

        // Cleanup must be reliable even when the print dialog is cancelled.
        // Some browsers don't always fire `afterprint`, so we also use `focus` + `matchMedia('print')` + a failsafe timer.
        let cleanedUp = false;
        let failSafeTimer: number | undefined;
        let mediaQuery: MediaQueryList | null = null;
        let exitButton: HTMLButtonElement | null = null;
        const handleKeyDown = (e: KeyboardEvent) => {
          if (e.key === "Escape") cleanupOnce();
        };
        const handleMediaChange = (e: MediaQueryListEvent) => {
          // when leaving print mode, e.matches becomes false
          if (!e.matches) {
            cleanupOnce();
          }
        };
        const handleFocus = () => {
          // focus comes back when the dialog is closed/cancelled
          setTimeout(() => cleanupOnce(), 150);
        };
        const handleAfterPrint = () => cleanupOnce();

        const cleanupOnce = () => {
          if (cleanedUp) return;
          cleanedUp = true;

          try {
            cleanup();
          } finally {
            window.removeEventListener("afterprint", handleAfterPrint);
            window.removeEventListener("focus", handleFocus);
            window.removeEventListener("keydown", handleKeyDown);
            if (window.onafterprint === handleAfterPrint) {
              window.onafterprint = null;
            }
            if (mediaQuery) {
              try {
                // modern browsers
                // @ts-ignore - older TS DOM lib can miss this signature
                mediaQuery.removeEventListener?.("change", handleMediaChange);
                // legacy safari
                // @ts-ignore
                mediaQuery.removeListener?.(handleMediaChange);
              } catch {
                // ignore
              }
            }
            if (failSafeTimer) {
              window.clearTimeout(failSafeTimer);
            }
            if (exitButton) {
              try {
                exitButton.remove();
              } catch {
                // ignore
              }
              exitButton = null;
            }
          }
        };

        window.addEventListener("afterprint", handleAfterPrint);
        window.addEventListener("focus", handleFocus);
        window.addEventListener("keydown", handleKeyDown);
        window.onafterprint = handleAfterPrint;
        try {
          mediaQuery = window.matchMedia("print");
          // @ts-ignore - older TS DOM lib can miss this signature
          mediaQuery.addEventListener?.("change", handleMediaChange);
          // @ts-ignore
          mediaQuery.addListener?.(handleMediaChange);
        } catch {
          mediaQuery = null;
        }
        // failsafe cleanup in case no events fire
        failSafeTimer = window.setTimeout(() => cleanupOnce(), 15000);

        // Manual exit button in case print dialog doesn't open or afterprint never fires.
        try {
          exitButton = document.createElement("button");
          exitButton.type = "button";
          exitButton.className = "print-exit-button";
          exitButton.textContent = "Close Preview (Esc)";
          exitButton.addEventListener("click", () => cleanupOnce());
          printContainer?.appendChild(exitButton);
        } catch {
          exitButton = null;
        }

        // Small delay to ensure styles are applied and DOM is ready
        // For external reports, wait a bit longer to ensure print fix is applied
        const delay = formType === "externalReport" ? 200 : 100;
        setTimeout(() => {
          try {
            // CRITICAL: Force borders on all table cells to ensure continuation pages have borders
            // When a cell's content continues to another page, the continuation MUST have full borders
            // EXCEPT for eval-compact tables which have their own ultra-thin borders
            if (printContainer) {
              // Get all cells EXCEPT those in eval-compact tables
              const allCells = printContainer.querySelectorAll('table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) td, table.bsuFormChild:not(.eval-compact):not(.compact.eval-compact) th');
              allCells.forEach((cell) => {
                const htmlCell = cell as HTMLElement;
                // PRIMARY: Force all borders with inline styles
                htmlCell.style.setProperty('border', '1px solid #000', 'important');
                htmlCell.style.setProperty('border-top', '1px solid #000', 'important');
                htmlCell.style.setProperty('border-bottom', '1px solid #000', 'important');
                htmlCell.style.setProperty('border-left', '1px solid #000', 'important');
                htmlCell.style.setProperty('border-right', '1px solid #000', 'important');
                htmlCell.style.setProperty('border-style', 'solid', 'important');
                htmlCell.style.setProperty('border-width', '1px', 'important');
                htmlCell.style.setProperty('border-color', '#000', 'important');
                
                // CRITICAL: Add outline as backup border method for page breaks - lighter borders
                // Outline is more reliable on continuation pages when cells break across pages
                htmlCell.style.setProperty('outline', '0.5px solid #666', 'important');
                htmlCell.style.setProperty('outline-offset', '-0.5px', 'important');
                htmlCell.style.setProperty('outline-style', 'solid', 'important');
                htmlCell.style.setProperty('outline-width', '0.5px', 'important');
                htmlCell.style.setProperty('outline-color', '#666', 'important');
                
                // Ensure borders are visible in print
                htmlCell.style.setProperty('-webkit-print-color-adjust', 'exact', 'important');
                htmlCell.style.setProperty('print-color-adjust', 'exact', 'important');
              });
              
              // CRITICAL: Set ultra-thin black borders for eval-compact and financial-plan tables
              // Remove ALL existing borders first, then apply black
              const evalCompactCells = printContainer.querySelectorAll('table.bsuFormChild.eval-compact td, table.bsuFormChild.eval-compact th, table.bsuFormChild.compact.eval-compact td, table.bsuFormChild.compact.eval-compact th, table.bsuFormChild.financial-plan td, table.bsuFormChild.financial-plan th');
              evalCompactCells.forEach((cell) => {
                const htmlCell = cell as HTMLElement;
                // FIRST: Remove any black borders completely
                htmlCell.style.removeProperty('border');
                htmlCell.style.removeProperty('border-top');
                htmlCell.style.removeProperty('border-bottom');
                htmlCell.style.removeProperty('border-left');
                htmlCell.style.removeProperty('border-right');
                htmlCell.style.removeProperty('outline');
                htmlCell.style.removeProperty('outline-top');
                htmlCell.style.removeProperty('outline-bottom');
                htmlCell.style.removeProperty('outline-left');
                htmlCell.style.removeProperty('outline-right');
                
                // THEN: Force ultra-thin black borders only
                htmlCell.style.setProperty('border', '0.5px solid #000', 'important');
                htmlCell.style.setProperty('border-top', '0.5px solid #000', 'important');
                htmlCell.style.setProperty('border-bottom', '0.5px solid #000', 'important');
                htmlCell.style.setProperty('border-left', '0.5px solid #000', 'important');
                htmlCell.style.setProperty('border-right', '0.5px solid #000', 'important');
                htmlCell.style.setProperty('border-style', 'solid', 'important');
                htmlCell.style.setProperty('border-width', '0.5px', 'important');
                htmlCell.style.setProperty('border-color', '#000', 'important');
                
                // Remove outline completely to prevent double border (bold appearance)
                htmlCell.style.setProperty('outline', 'none', 'important');
                htmlCell.style.setProperty('outline-offset', '0', 'important');
                htmlCell.style.setProperty('outline-style', 'none', 'important');
                htmlCell.style.setProperty('outline-width', '0', 'important');
                htmlCell.style.setProperty('outline-color', 'transparent', 'important');
                
                // Ensure borders are visible in print
                htmlCell.style.setProperty('-webkit-print-color-adjust', 'exact', 'important');
                htmlCell.style.setProperty('print-color-adjust', 'exact', 'important');
              });
              
              // Also set border on eval-compact and financial-plan tables themselves - remove black first
              const evalCompactTables = printContainer.querySelectorAll('table.bsuFormChild.eval-compact, table.bsuFormChild.compact.eval-compact, table.bsuFormChild.financial-plan');
              evalCompactTables.forEach((table) => {
                const htmlTable = table as HTMLElement;
                // Remove any black borders first
                htmlTable.style.removeProperty('border');
                htmlTable.style.removeProperty('border-top');
                htmlTable.style.removeProperty('border-bottom');
                htmlTable.style.removeProperty('border-left');
                htmlTable.style.removeProperty('border-right');
                htmlTable.style.removeProperty('outline');
                
                // Then apply black only
                htmlTable.style.setProperty('border', '0.5px solid #000', 'important');
                htmlTable.style.setProperty('border-top', '0.5px solid #000', 'important');
                htmlTable.style.setProperty('border-bottom', '0.5px solid #000', 'important');
                htmlTable.style.setProperty('border-left', '0.5px solid #000', 'important');
                htmlTable.style.setProperty('border-right', '0.5px solid #000', 'important');
                htmlTable.style.setProperty('-webkit-print-color-adjust', 'exact', 'important');
                htmlTable.style.setProperty('print-color-adjust', 'exact', 'important');
              });

              // Ensure all tables use border-collapse
              const allTables = printContainer.querySelectorAll('table.bsuFormChild');
              allTables.forEach((table) => {
                const htmlTable = table as HTMLElement;
                htmlTable.style.setProperty('border-collapse', 'collapse', 'important');
                htmlTable.style.setProperty('border-spacing', '0', 'important');
              });
            }

            // One final application of print fix for external reports
            if (formType === "externalReport" && printContainer) {
              const ulElements = printContainer.querySelectorAll('td ul, th ul');
              ulElements.forEach((el) => {
                const htmlEl = el as HTMLElement;
                htmlEl.style.removeProperty('margin');
                htmlEl.style.setProperty('margin-top', '1px', 'important');
                htmlEl.style.setProperty('margin-bottom', '1px', 'important');
                htmlEl.style.setProperty('padding-top', '0', 'important');
                htmlEl.style.setProperty('padding-bottom', '0', 'important');
              });
              
              const liElements = printContainer.querySelectorAll('td ul li, th ul li');
              liElements.forEach((el) => {
                const htmlEl = el as HTMLElement;
                htmlEl.style.removeProperty('margin');
                htmlEl.style.setProperty('margin-top', '0', 'important');
                htmlEl.style.setProperty('margin-bottom', '0', 'important');
                htmlEl.style.setProperty('padding-top', '0', 'important');
                htmlEl.style.setProperty('padding-bottom', '0', 'important');
                htmlEl.style.setProperty('line-height', '1.2', 'important');
              });
            }
          } catch (error) {
            console.error("Error in final print fix application:", error);
            // Continue with print even if fix fails
          }

          // Footer removed by request
          
          void printContainer?.offsetHeight;
        window.print();
        }, delay);
      }; // end checkReady

      checkReady();
    }; // end preparePrint

    // initial delay to let React mount
    setTimeout(preparePrint, 400);
  };

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        // Validate data exists
        if (!data) {
          console.warn("FormDataLoaderModal: No data provided");
          setFormTemplate(<></>);
          return;
        }

        if ((formType === "externalEvent" || formType === "internalEvent") && data?.id) {
          const type = formType === "externalEvent" ? "external" : "internal";
          // Ensure id is a valid number
          const eventId = typeof data.id === "number" ? data.id : parseInt(data.id, 10);
          
          if (isNaN(eventId)) {
            console.error(`FormDataLoaderModal: Invalid event ID: ${data.id}`);
            // Fall through to use original data
          } else {
            try {
              const res = await getEventDetails(eventId, type);
              
              // Check if response is valid - API returns res.data.data.event
              // Backend structure: { data: { event: {...}, registered: number, attended: number }, message: string }
              if (res?.data?.data?.event) {
                const fresh = res.data.data.event;
                
                // If signatoriesId exists and is a number (not an object), fetch the signatory data
                if (fresh.signatoriesId && typeof fresh.signatoriesId === 'number') {
                  try {
                    const signatoryRes = await getSignatory(fresh.signatoriesId);
                    if (signatoryRes?.data?.data) {
                      fresh.signatoriesId = signatoryRes.data.data;
                    }
                  } catch (signatoryError: any) {
                    console.warn(`Failed to fetch signatory data for ID ${fresh.signatoriesId}:`, signatoryError);
                    // Continue without signatory data
                  }
                }
                
                if (!isMounted) return;
                if (formType === "externalEvent") {
                  setFormTemplate(<ExternalEventForm data={fresh} />);
                } else {
                  setFormTemplate(<InternalEventForm data={fresh} />);
                }
                return;
              } else if (res?.data?.data) {
                // Fallback: if data exists but no event property, use the data directly
                const fresh = res.data.data;
                
                // If signatoriesId exists and is a number (not an object), fetch the signatory data
                if (fresh.signatoriesId && typeof fresh.signatoriesId === 'number') {
                  try {
                    const signatoryRes = await getSignatory(fresh.signatoriesId);
                    if (signatoryRes?.data?.data) {
                      fresh.signatoriesId = signatoryRes.data.data;
                    }
                  } catch (signatoryError: any) {
                    console.warn(`Failed to fetch signatory data for ID ${fresh.signatoriesId}:`, signatoryError);
                    // Continue without signatory data
                  }
                }
                
                if (!isMounted) return;
                if (formType === "externalEvent") {
                  setFormTemplate(<ExternalEventForm data={fresh} />);
                } else {
                  setFormTemplate(<InternalEventForm data={fresh} />);
                }
                return;
              } else {
                console.warn("FormDataLoaderModal: API response missing event data, using fallback");
              }
            } catch (apiError: any) {
              // Log the error but continue with fallback
              // Handle both axios error structure and direct error responses
              const statusCode = apiError?.response?.status || apiError?.status;
              const errorMessage = apiError?.response?.data?.message || 
                                 apiError?.response?.data?.error || 
                                 apiError?.message || 
                                 "Unknown error";
              
              // Only log as error if it's not a 404 (not found is expected in some cases)
              if (statusCode === 404) {
                console.warn(`Event ${eventId} (${type}) not found, using provided data`);
              } else {
                console.error(`Error fetching event details for ${type} event ${eventId} (Status: ${statusCode}):`, errorMessage);
              }
              // Fall through to use original data as fallback
            }
          }
        }

        // fallback - render with provided data
        if (!isMounted) return;
        
        // Ensure data is always an object, never null/undefined
        const safeData = data || {};
        
        // If signatoriesId exists and is a number (not an object), fetch the signatory data
        if (safeData.signatoriesId && typeof safeData.signatoriesId === 'number' && (formType === "externalEvent" || formType === "internalEvent")) {
          try {
            const signatoryRes = await getSignatory(safeData.signatoriesId);
            if (signatoryRes?.data?.data && isMounted) {
              safeData.signatoriesId = signatoryRes.data.data;
            }
          } catch (signatoryError: any) {
            console.warn(`Failed to fetch signatory data for ID ${safeData.signatoriesId}:`, signatoryError);
            // Continue without signatory data
          }
        }
        
        if (!isMounted) return;
        
        switch (formType) {
          case "externalEvent":
            setFormTemplate(<ExternalEventForm data={safeData} />);
            break;
          case "internalEvent":
            setFormTemplate(<InternalEventForm data={safeData} />);
            break;
          case "evaluation":
            setFormTemplate(<EvaluationForm />);
            break;
          case "externalReport":
            setFormTemplate(<ExternalReport textAlign={textAlign} data={safeData} />);
            break;
          case "internalReport":
            setFormTemplate(<InternalReport textAlign={textAlign} data={safeData} />);
            break;
          default:
            console.warn(`FormDataLoaderModal: Unknown formType: ${formType}`);
            setFormTemplate(<></>);
        }
      } catch (error: any) {
        console.error("Error in FormDataLoaderModal useEffect:", error);
        if (!isMounted) return;
        // Last resort fallback
        try {
          if (formType === "externalEvent" || formType === "internalEvent") {
            if (formType === "externalEvent") {
              setFormTemplate(<ExternalEventForm data={data || {}} />);
            } else {
              setFormTemplate(<InternalEventForm data={data || {}} />);
            }
          } else {
            setFormTemplate(<></>);
          }
        } catch (renderError) {
          console.error("Error rendering fallback form:", renderError);
          setFormTemplate(<></>);
        }
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [formType, data, textAlign]);

  return (
    <PopupModal header="Form Preview" open={open} setOpen={setOpen} minWidth="7in" maxWidth="7in">
      <Box maxHeight="50vh" overflow="auto" sx={{ scrollbarWidth: "thin" }}>
        {formTemplate}
      </Box>
      {!hidePrintButton && (
        <FlexBox paddingTop="20px" justifyContent="flex-end" gap="10px">
          {beforePrintComponent}
          <PrimaryButton label="Print" startIcon={<LocalPrintshopIcon />} sx={{ minWidth: "125px" }} onClick={() => printForm()} />
        </FlexBox>
      )}
    </PopupModal>
  );
};

export default FormDataLoaderModal; 