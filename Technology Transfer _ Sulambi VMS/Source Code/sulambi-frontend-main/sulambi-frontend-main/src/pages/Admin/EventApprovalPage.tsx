import { useContext, useEffect, useState } from "react";
import TextHeader from "../../components/Headers/TextHeader";
import TextSubHeader from "../../components/Headers/TextSubHeader";
import ConfirmModal from "../../components/Modal/ConfirmModal";
import DataTable from "../../components/Tables/DataTable";
import PageLayout from "../PageLayout";
import { Box, CircularProgress, Typography } from "@mui/material";
import FlexBox from "../../components/FlexBox";

import FeedbackIcon from "@mui/icons-material/Feedback";
import RemoveRedEyeIcon from "@mui/icons-material/RemoveRedEye";
import ThumbDownIcon from "@mui/icons-material/ThumbDown";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import CustomDropdown from "../../components/Inputs/CustomDropdown";
import {
  acceptExternalEvent,
  acceptInternalEvent,
  getAllEvents,
  rejectExternalEvent,
  rejectInternalEvent,
} from "../../api/events";
import {
  ExternalEventProposalType,
  InternalEventProposalType,
} from "../../interface/types";
import Chip from "../../components/Chips/Chip";
import MenuButtonTemplate from "../../components/Menu/MenuButtonTemplate";
import BarChartIcon from "@mui/icons-material/BarChart";
import FormDataLoaderModal from "../../components/Modal/FormDataLoaderModal";
import { SnackbarContext } from "../../contexts/SnackbarProvider";
import EvaluationList from "../../components/Popups/EvaluationList";
import FindInPageIcon from "@mui/icons-material/FindInPage";
import LatentAnalysisList from "../../components/Popups/LatentAnalysisList";
import PrimaryButton from "../../components/Buttons/PrimaryButton";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import VisibilityIcon from "@mui/icons-material/Visibility";
import HistoryEduIcon from "@mui/icons-material/HistoryEdu";
import SignatoriesForm from "../../components/Forms/SignatoriesForm";
import { useSearchParams } from "react-router-dom";
import FeedbackForm from "../../components/Forms/FeedbackForm";
import { useCachedFetch } from "../../hooks/useCachedFetch";
import { CACHE_TIMES } from "../../utils/apiCache";

const EventApproval = () => {
  const { showSnackbarMessage } = useContext(SnackbarContext);
  const [searchParams] = useSearchParams();

  const [searchVal, setSearchVal] = useState("");
  const [refreshTable, setRefreshTable] = useState(0);
  const [actionName, setActionName] = useState<"Reject" | "Approve">("Reject");
  const [targetId, setTargetId] = useState<number>();
  const [targetType, setTargetType] = useState("");
  const [signatoryId, setSignatoryId] = useState<number>();
  const [openSignatoryModal, setOpenSignatoryModal] = useState(false);
  const [openFeedbackDialog, setOpenFeedbackDialog] = useState(false);
  const [feedbackId, setFeedbackId] = useState<number | undefined>();

  const [searchFilter, setSearchFilter] = useState({
    searchText: "",
    status: searchParams.get("status") ?? "",
    type: searchParams.get("type") ?? "",
  });

  const [openDialog, setOpenDialog] = useState(false);
  const [tableData, setTableData] = useState<any[]>([]);

  const [hideReportedEvents, setHideReportedEvents] = useState(false);
  const [showFormPreview, setShowFormPreview] = useState(false);
  const [selectedFormData, setSelectedFormData] = useState<any>({});
  const [selectedFormType, setSelectedFormType] = useState<
    "external" | "internal"
  >("external");

  const chipMap = {
    editing: <Chip bgcolor="blue" label="editing" color="white" />,
    submitted: (
      <Chip bgcolor="#a3a300" label="submitted proposal" color="white" />
    ),
    accepted: (
      <Chip bgcolor="#2f7a00" label="proposal approved" color="white" />
    ),
    rejected: (
      <Chip bgcolor="#c10303" label="proposal rejected" color="white" />
    ),
  };

  const [showEvaluationList, setShowEvaluationList] = useState(false);
  const [showEventAnalysis, setShowEventAnalysis] = useState(false);

  // Use cached fetch - data persists when navigating away and coming back!
  const { data: eventsResponse, loading } = useCachedFetch({
    cacheKey: 'event_approval_events',
    fetchFn: () => getAllEvents(),
    cacheTime: CACHE_TIMES.SHORT, // Refresh every 30 seconds (approval page needs fresher data)
    useMemoryCache: true,
  });

  // Process events data when response changes or filters change
  useEffect(() => {
    if (!eventsResponse) return;

    // Combine external and internal events (check both possible response structures)
    const eventData: (ExternalEventProposalType | InternalEventProposalType)[] = 
      eventsResponse.events || 
      [...(eventsResponse.external || []), ...(eventsResponse.internal || [])];

    const filteredData = eventData
      .filter((event: any) => {
        return (
          event.title.toLowerCase().includes(searchVal) ||
          event.status.toLowerCase().includes(searchVal)
        );
      })
      .filter((event: any) => {
        if (searchFilter.type === "") return true;
        return event.eventTypeIndicator === searchFilter.type;
      })
      .filter((event) => {
        if (event.hasReport && hideReportedEvents) return false;
        return true;
      })
      .filter((event) => {
        if (searchFilter.status !== "")
          return event.status === searchFilter.status;
        return true;
      })
      .map((event: any) => {
        return [
          event.createdBy.username,
          event.title,
          event.eventTypeIndicator,
          chipMap[
            event.status as
              | "editing"
              | "submitted"
              | "accepted"
              | "rejected"
          ],
          event.status === "submitted" ? (
            <MenuButtonTemplate
              items={[
                {
                  label: "View",
                  icon: <RemoveRedEyeIcon />,
                  onClick: () => {
                    setSelectedFormType(event.eventTypeIndicator);
                    setSelectedFormData(event);
                    setShowFormPreview(true);
                  },
                },
                {
                  label: "Approve Event",
                  icon: <ThumbUpIcon />,
                  onClick: () => {
                    setTargetId(event.id);
                    setTargetType(event.eventTypeIndicator);
                    setActionName("Approve");
                    setOpenDialog(true);
                  },
                },
                {
                  label: "Reject Event",
                  icon: <ThumbDownIcon />,
                  onClick: () => {
                    setTargetId(event.id);
                    setTargetType(event.eventTypeIndicator);
                    setActionName("Reject");
                    setOpenDialog(true);
                  },
                },
                {
                  label: `${
                    !!event.feedback_id ? "Edit" : "Submit"
                  } Feedback`,
                  icon: <FeedbackIcon />,
                  onClick: () => {
                    setTargetId(event.id);
                    setSelectedFormType(event.eventTypeIndicator);
                    if (event.feedback_id !== null) {
                      setFeedbackId(event.feedback_id);
                    }

                    setOpenFeedbackDialog(true);
                  },
                },
              ]}
            />
          ) : (
            <MenuButtonTemplate
              items={[
                {
                  label: "View",
                  icon: <RemoveRedEyeIcon />,
                  onClick: () => {
                    setSelectedFormType(event.eventTypeIndicator);
                    setSelectedFormData(event);
                    setShowFormPreview(true);
                  },
                },
                {
                  label: "View Evaluations",
                  icon: <FindInPageIcon />,
                  onClick: () => {
                    setSelectedFormType(event.eventTypeIndicator);
                    setSelectedFormData(event);
                    setShowEvaluationList(true);
                  },
                },
                {
                  label: "View Analysis",
                  icon: <BarChartIcon />,
                  onClick: () => {
                    setSelectedFormType(event.eventTypeIndicator);
                    setSelectedFormData(event);
                    setShowEventAnalysis(true);
                  },
                },
              ].concat(
                []
              )}
            />
          ),
        ];
      });

    setTableData(filteredData);
  }, [eventsResponse, refreshTable, searchFilter, hideReportedEvents, searchVal]);

  const CustomComponents = [
    <CustomDropdown
      width="200px"
      label="Status"
      initialValue={searchFilter.status}
      menu={[
        { key: "All", value: "" },
        { key: "Proposal Approved", value: "accepted" },
        { key: "Proposal Rejected", value: "rejected" },
        { key: "Submitted Proposal", value: "submitted" },
      ]}
      onChange={(event) => {
        setSearchFilter({
          ...searchFilter,
          status: event.target.value,
        });
      }}
    />,
    <CustomDropdown
      width="200px"
      label="Proposal Type"
      menu={[
        { key: "All", value: "" },
        { key: "Internal", value: "internal" },
        { key: "External", value: "external" },
      ]}
      onChange={(event) => {
        setSearchFilter({
          ...searchFilter,
          type: event.target.value,
        });
      }}
    />,
  ];

  const CustomLeftComponents = [
    <PrimaryButton
      label={`${hideReportedEvents ? "Show" : "Hide"} Reported Events`}
      startIcon={
        hideReportedEvents ? <VisibilityIcon /> : <VisibilityOffIcon />
      }
      sx={{
        backgroundColor: hideReportedEvents
          ? "var(--text-landing)"
          : "var(--button-red)",
      }}
      onClick={() => {
        setHideReportedEvents(!hideReportedEvents);
      }}
    />,
  ];

  return (
    <>
      <ConfirmModal
        open={openDialog}
        setOpen={setOpenDialog}
        title="Event Proposal"
        message={`Are you sure you want to ${actionName} this proposal?`}
        acceptText="Yes"
        declineText="Cancel"
        onAccept={() => {
          if (targetType === "external") {
            if (actionName === "Approve") {
              targetId !== undefined &&
                acceptExternalEvent(targetId)
                  .then(() => {
                    showSnackbarMessage(
                      "External event successfully approved!",
                      "success"
                    );
                  })
                  .catch(() => {
                    showSnackbarMessage(
                      "Error occured in approving event",
                      "error"
                    );
                  })
                  .finally(() => setRefreshTable(refreshTable + 1));
            }

            if (actionName === "Reject") {
              targetId !== undefined &&
                rejectExternalEvent(targetId)
                  .then(() => {
                    showSnackbarMessage(
                      "External event successfully rejected!",
                      "success"
                    );
                  })
                  .catch(() => {
                    showSnackbarMessage(
                      "Error occured in rejecting event",
                      "error"
                    );
                  })
                  .finally(() => setRefreshTable(refreshTable + 1));
            }
          }

          if (targetType === "internal") {
            if (actionName === "Approve") {
              targetId !== undefined &&
                acceptInternalEvent(targetId)
                  .then(() => {
                    showSnackbarMessage(
                      "Internal event successfully approved!",
                      "success"
                    );
                  })
                  .catch(() => {
                    showSnackbarMessage(
                      "Error occured in approving event",
                      "success"
                    );
                  })
                  .finally(() => setRefreshTable(refreshTable + 1));
            }

            if (actionName === "Reject") {
              targetId !== undefined &&
                rejectInternalEvent(targetId)
                  .then(() => {
                    showSnackbarMessage(
                      "Internal event successfully rejected!",
                      "success"
                    );
                  })
                  .catch(() => {
                    showSnackbarMessage(
                      "Error occured in rejecting event",
                      "error"
                    );
                  })
                  .finally(() => setRefreshTable(refreshTable + 1));
            }
          }
        }}
      />
      {!!signatoryId && (
        <SignatoriesForm
          signatoryId={signatoryId}
          open={openSignatoryModal}
          setOpen={setOpenSignatoryModal}
          onSave={() => setShowFormPreview(false)}
        />
      )}
      {targetId && openFeedbackDialog && (
        <FeedbackForm
          eventId={targetId}
          eventType={selectedFormType as "external" | "internal"}
          feedbackId={feedbackId}
          open={openFeedbackDialog}
          setOpen={setOpenFeedbackDialog}
          onClose={() => {
            setRefreshTable(refreshTable + 1);
            setTargetId(undefined);
            setFeedbackId(undefined);
          }}
        />
      )}
      <EvaluationList
        open={showEvaluationList}
        selectedFormData={selectedFormData}
        selectedFormType={selectedFormType as "external" | "internal"}
        setOpen={setShowEvaluationList}
      />
      <LatentAnalysisList
        eventId={selectedFormData.id}
        eventType={selectedFormType as "external" | "internal"}
        open={showEventAnalysis}
        setOpen={setShowEventAnalysis}
      />
      <FormDataLoaderModal
        formType={
          selectedFormType === "external" ? "externalEvent" : "internalEvent"
        }
        data={selectedFormData}
        open={showFormPreview}
        setOpen={setShowFormPreview}
        beforePrintComponent={
          <PrimaryButton
            label="Update Signatories"
            startIcon={<HistoryEduIcon />}
            onClick={() => {
              setSignatoryId(selectedFormData?.signatoriesId?.id ?? null);
              setOpenSignatoryModal(true);
            }}
          />
        }
      />
      <PageLayout page="event-approval">
        <TextHeader>EVENT APPROVAL</TextHeader>
        <TextSubHeader>View and Manage Proposed events</TextSubHeader>
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
              Loading Events...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please wait while we fetch the event data
            </Typography>
          </FlexBox>
        ) : (
          <DataTable
            title="Event Approval Table"
            fields={[
              "Officer Username",
              "Event Name",
              "Type",
              "Status",
              "Action",
            ]}
            componentOnLeft={[CustomLeftComponents]}
            componentBeforeSearch={CustomComponents}
            data={tableData}
            onSearch={(key) => setSearchVal(key.toLowerCase())}
          />
        )}
      </PageLayout>
    </>
  );
};

export default EventApproval;
