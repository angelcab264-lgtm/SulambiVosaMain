import { useContext, useEffect, useState } from "react";
import TextHeader from "../../components/Headers/TextHeader";
import TextSubHeader from "../../components/Headers/TextSubHeader";
import DataTable from "../../components/Tables/DataTable";
import PageLayout from "../PageLayout";
import RemoveRedEyeIcon from "@mui/icons-material/RemoveRedEye";
import { Box, CircularProgress, Typography } from "@mui/material";
import FlexBox from "../../components/FlexBox";

import { getAllReports, deleteReport } from "../../api/reports";
import { ExternalReportType, InternalReportType } from "../../interface/types";
import dayjs from "dayjs";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import MenuButtonTemplate from "../../components/Menu/MenuButtonTemplate";
import FormDataLoaderModal from "../../components/Modal/FormDataLoaderModal";
import PrimaryButton from "../../components/Buttons/PrimaryButton";
import HistoryEduIcon from "@mui/icons-material/HistoryEdu";
import SignatoriesForm from "../../components/Forms/SignatoriesForm";
import { FormDataContext } from "../../contexts/FormDataProvider";
import { SnackbarContext } from "../../contexts/SnackbarProvider";
import ConfirmModal from "../../components/Modal/ConfirmModal";
import { useCachedFetch } from "../../hooks/useCachedFetch";
import { CACHE_TIMES } from "../../utils/apiCache";

const ReportPage = () => {
  const { setFormData, resetFormData } = useContext(FormDataContext);
  const { showSnackbarMessage } = useContext(SnackbarContext);
  const [reportData, setReportData] = useState<any[]>([]);
  const [searchReport, setSearchReport] = useState("");
  const [textPos, setTextPos] = useState<"left" | "justify">("left");

  const [openUpdateSignatories, setOpenUpdateSignatories] = useState(false);
  const [openFormDataLoader, setOpenFormDataLoader] = useState(false);
  const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false);
  const [reportType, setReportType] = useState<
    "externalReport" | "internalReport"
  >("externalReport");
  const [selectedReport, setSelectedReport] = useState<
    ExternalReportType | InternalReportType
  >();
  const [reportToDelete, setReportToDelete] = useState<{
    id: number;
    type: "external" | "internal";
    title: string;
  } | null>(null);

  // Use cached fetch - data persists when navigating away and coming back!
  const { data: reportsResponse, loading, refetch: refetchReports } = useCachedFetch({
    cacheKey: 'reports_all',
    fetchFn: () => getAllReports(),
    cacheTime: CACHE_TIMES.MEDIUM, // Cache for 5 minutes
    useMemoryCache: true, // Fast memory cache for navigation
  });

  const viewExternalReportAction = (rowData: ExternalReportType) => {
    // Clear any existing form data to ensure clean state
    resetFormData();
    setReportType("externalReport");
    setSelectedReport(rowData);
    setOpenFormDataLoader(true);
  };

  const viewInternalReportAction = (rowData: InternalReportType) => {
    // Clear any existing form data to ensure clean state
    resetFormData();
    setReportType("internalReport");
    setSelectedReport(rowData);
    setOpenFormDataLoader(true);
  };

  const handleDeleteReport = (report: ExternalReportType | InternalReportType, type: "external" | "internal") => {
    console.log("Report to delete:", report);
    console.log("Report type:", type);
    console.log("Report ID:", (report as any).id);
    
    setReportToDelete({
      id: (report as any).id,
      type: type,
      title: report.eventId?.title || "Unknown Report"
    });
    setOpenDeleteConfirm(true);
  };

  const confirmDeleteReport = async () => {
    if (!reportToDelete) return;

    try {
      console.log(`Attempting to delete ${reportToDelete.type} report with ID: ${reportToDelete.id}`);
      
      const response = await deleteReport(reportToDelete.id, reportToDelete.type);
      console.log("Delete response:", response);
      
      showSnackbarMessage(
        `${reportToDelete.type === "external" ? "External" : "Internal"} report "${reportToDelete.title}" deleted successfully`,
        "success"
      );
      
      // Clear all form data to prevent residual data
      resetFormData();
      setSelectedReport(undefined);
      
      // Force close any open form modals to prevent residual state
      setOpenFormDataLoader(false);
      
      // Refresh the report list (fetch fresh data, skip cache)
      refetchReports(); // This will skip cache and fetch fresh data
      
      // Close confirmation modal
      setOpenDeleteConfirm(false);
      setReportToDelete(null);
      
    } catch (error: any) {
      console.error("Delete error:", error);
      console.error("Error response:", error.response);
      console.error("Error data:", error.response?.data);
      
      const errorMessage = error.response?.data?.message || error.message || "Failed to delete report";
      showSnackbarMessage(`Error: ${errorMessage}`, "error");
    }
  };

  // Process and filter reports data when response or search changes
  const refreshReportList = () => {
    if (!reportsResponse) return;

    const externalReport: ExternalReportType[] = reportsResponse.external || [];
    const internalReport: InternalReportType[] = reportsResponse.internal || [];

    console.log("External reports:", externalReport);
    console.log("Internal reports:", internalReport);

    const newReportData = [
        ...externalReport
          .filter((report) => {
            if (searchReport === "") return true;
            return (report.eventId?.title as string)
              .toLowerCase()
              .includes(searchReport.toLowerCase());
          })
          .map((report) => {
            return [
              report.eventId?.title,
              dayjs(report.eventId?.durationStart).format(
                "MMMM D, YYYY h:mm A"
              ),
              dayjs(report.eventId?.durationEnd).format("MMMM D, YYYY h:mm A"),
              <MenuButtonTemplate
                key={`external-${(report as any).id}`}
                items={[
                  {
                    label: "View Report",
                    icon: <RemoveRedEyeIcon />,
                    onClick: () => viewExternalReportAction(report),
                  },
                  {
                    label: "Delete Report",
                    icon: <DeleteForeverIcon />,
                    onClick: () => handleDeleteReport(report, "external"),
                  },
                ]}
              />,
            ];
          }),
        ...internalReport
          .filter((report) => {
            if (searchReport === "") return true;
            return (report.eventId?.title as string)
              .toLowerCase()
              .includes(searchReport.toLowerCase());
          })
          .map((report) => {
            return [
              report.eventId?.title,
              dayjs(report.eventId?.durationStart).format(
                "MMMM D, YYYY h:mm A"
              ),
              dayjs(report.eventId?.durationEnd).format("MMMM D, YYYY h:mm A"),
              <MenuButtonTemplate
                key={`internal-${(report as any).id}`}
                items={[
                  {
                    label: "View Report",
                    icon: <RemoveRedEyeIcon />,
                    onClick: () => viewInternalReportAction(report),
                  },
                  { 
                    label: "Delete Report", 
                    icon: <DeleteForeverIcon />,
                    onClick: () => handleDeleteReport(report, "internal"),
                  },
                ]}
              />,
            ];
          }),
      ];
      
    console.log("New report data:", newReportData);
    setReportData(newReportData);
  };

  // Process reports when cached data changes or search changes
  useEffect(() => {
    refreshReportList();
  }, [reportsResponse, searchReport]);

  return (
    <>
      {selectedReport && (
        <SignatoriesForm
          signatoryId={selectedReport?.signatoriesId?.id}
          open={openUpdateSignatories}
          setOpen={setOpenUpdateSignatories}
          onSave={() => {
            setFormData({});
            setOpenFormDataLoader(false);
            setOpenUpdateSignatories(false);
            refetchReports(); // Refresh reports data
          }}
        />
      )}
      <ConfirmModal
        title="Delete Report"
        message={`Are you sure you want to delete the report "${reportToDelete?.title}"? This action cannot be undone.`}
        acceptText="Delete"
        declineText="Cancel"
        open={openDeleteConfirm}
        setOpen={setOpenDeleteConfirm}
        onAccept={confirmDeleteReport}
      />
      <FormDataLoaderModal
        open={openFormDataLoader}
        data={selectedReport}
        formType={reportType}
        textAlign={textPos}
        setOpen={(open) => {
          setOpenFormDataLoader(open);
          // Clear form data when modal closes to prevent state persistence issues
          if (!open) {
            resetFormData();
            setSelectedReport(undefined);
          }
        }}
        beforePrintComponent={[
          <PrimaryButton
            label={`Align text to ${textPos === "left" ? "Justify" : "Left"}`}
            startIcon={<HistoryEduIcon />}
            sx={{
              backgroundColor:
                textPos === "left" ? "var(--text-landing)" : "orange",
            }}
            onClick={() => {
              if (textPos === "left") setTextPos("justify");
              else setTextPos("left");
            }}
          />,
          <PrimaryButton
            label="Update Signatories"
            startIcon={<HistoryEduIcon />}
            onClick={() => {
              setOpenUpdateSignatories(true);
            }}
          />,
        ]}
      />
      <PageLayout page="report">
        <TextHeader>REPORTS</TextHeader>
        <TextSubHeader>Manage and Submit your reports</TextSubHeader>
        {loading ? (
          <FlexBox
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            minHeight="60vh"
            gap={2}
          >
            <CircularProgress size={60} />
            <Typography variant="h6" color="text.secondary">
              Loading Reports...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please wait while we fetch the report data
            </Typography>
          </FlexBox>
        ) : (
          <DataTable
            title="Reports Table"
            fields={[
              "Event Title",
              "Event Start Date",
              "Event End Date",
              "Action",
            ]}
            data={reportData}
            onSearch={(key) => {
              setSearchReport(key);
            }}
          />
        )}
      </PageLayout>
    </>
  );
};

export default ReportPage;
