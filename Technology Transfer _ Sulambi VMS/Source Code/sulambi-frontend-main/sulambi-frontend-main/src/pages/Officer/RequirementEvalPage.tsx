import { useContext, useEffect, useState } from "react";
import TextHeader from "../../components/Headers/TextHeader";
import TextSubHeader from "../../components/Headers/TextSubHeader";
import DataTable from "../../components/Tables/DataTable";
import PageLayout from "../PageLayout";
import {
  acceptRequirement,
  getAllRequirements,
  rejectRequirement,
} from "../../api/requirements";
import { RequirementsDataType } from "../../interface/types";
import Chip from "../../components/Chips/Chip";
import MenuButtonTemplate from "../../components/Menu/MenuButtonTemplate";

import RemoveRedEyeIcon from "@mui/icons-material/RemoveRedEye";
import ThumbDownIcon from "@mui/icons-material/ThumbDown";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import { SnackbarContext } from "../../contexts/SnackbarProvider";
// import { IconButton } from "@mui/material";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import RequirementForm from "../../components/Forms/RequirementForm";
import { FormDataContext } from "../../contexts/FormDataProvider";
import CustomDropdown from "../../components/Inputs/CustomDropdown";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../../components/Loading/LoadingSpinner";
import { Typography, Box } from "@mui/material";

const RequirementEvalPage = () => {
  const { showSnackbarMessage } = useContext(SnackbarContext);
  const { setFormData } = useContext(FormDataContext);
  const navigate = useNavigate();

  const [searchStatus, setSearchStatus] = useState(3);
  const [searchVal, setSearchVal] = useState("");
  const [debouncedSearchVal, setDebouncedSearchVal] = useState("");
  const [tableData, setTableData] = useState<any[]>([]);
  const [forceRefresh, setForceRefresh] = useState(0);
  const [loading, setLoading] = useState(true);

  const [selectedFormData, setSelectedFormData] = useState<any>({});
  const [viewFormData, setViewFormData] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    const accountType = localStorage.getItem("accountType");
    
    if (!token || !accountType) {
      console.warn("⚠️ No authentication token found, redirecting to login");
      showSnackbarMessage("Please log in to access this page", "warning");
      navigate("/login");
      return;
    }
    
    // Verify account type is officer or admin
    if (accountType !== "officer" && accountType !== "admin") {
      console.warn("⚠️ Insufficient permissions, redirecting to login");
      showSnackbarMessage("You don't have permission to access this page", "error");
      navigate("/login");
      return;
    }
    
    console.log("✅ Authentication check passed:", { accountType, hasToken: !!token });
  }, [navigate, showSnackbarMessage]);

  // Debounce search input to improve performance
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchVal(searchVal);
    }, 300); // 300ms delay

    return () => clearTimeout(timer);
  }, [searchVal]);

  useEffect(() => {
    setLoading(true);
    getAllRequirements()
      .then((response) => {
        console.log("Full API response:", response);
        console.log("Response data:", response?.data);
        
        // Ensure response has the expected structure
        if (!response?.data?.data) {
          console.warn("Invalid response structure:", response);
          console.warn("Response keys:", Object.keys(response?.data || {}));
          setTableData([]);
          setLoading(false);
          showSnackbarMessage(
            "Invalid response format from server",
            "error"
          );
          return;
        }

        const requirementsData: RequirementsDataType[] = response.data.data;

        // Check if requirementsData is an array
        if (!Array.isArray(requirementsData)) {
          console.warn("Requirements data is not an array:", requirementsData);
          console.warn("Type of requirementsData:", typeof requirementsData);
          setTableData([]);
          setLoading(false);
          showSnackbarMessage(
            "Requirements data format error",
            "error"
          );
          return;
        }

        console.log("✅ Fetched requirements:", requirementsData.length, "items");
        if (requirementsData.length > 0) {
          console.log("Sample requirement keys:", Object.keys(requirementsData[0]));
          console.log("Sample requirement:", requirementsData[0]);
          console.log("eventId value:", requirementsData[0].eventId);
          console.log("eventid value:", (requirementsData[0] as any).eventid);
        }
        console.log("Current search filter:", { searchVal: debouncedSearchVal, searchStatus });

      const chipMap = {
        notEvaluated: (
          <Chip bgcolor="blue" label="not-evaluated" color="white" />
        ),
        approved: <Chip bgcolor="#2f7a00" label="approved" color="white" />,
        rejected: <Chip bgcolor="#c10303" label="rejected" color="white" />,
      };

      // Normalize data - handle both camelCase and lowercase column names
      // Also ensure eventId is properly formatted
      const normalizedData = requirementsData.map((req: any) => {
        // Handle eventId - could be object, number, or lowercase key
        let eventId = req.eventId || req.eventid;
        
        // If eventId is still a number, it means backend didn't process it
        // Create a placeholder object
        if (typeof eventId === 'number' || typeof eventId === 'string') {
          eventId = {
            id: eventId,
            title: `Event ID ${eventId}`,
            status: "unknown"
          };
        }
        
        // Ensure accepted is properly typed (null, 0, 1, or undefined)
        let accepted = req.accepted;
        if (accepted === undefined && req.accepted === null) {
          accepted = null;
        }
        
        return {
          ...req,
          eventId: eventId,
          accepted: accepted,
        };
      });

      // Log each requirement before filtering
      normalizedData.forEach((req, index) => {
        console.log(`Requirement ${index}:`, {
          id: req.id,
          eventId: req.eventId,
          eventTitle: typeof req.eventId === 'object' ? req.eventId?.title : 'N/A',
          fullname: req.fullname,
          email: req.email,
          type: req.type,
          accepted: req.accepted,
        });
      });

      const afterSearchFilter = normalizedData
          .filter((req) => {
            // Use debounced search value
            if (!debouncedSearchVal || debouncedSearchVal.trim() === "") return true;
            
            const searchLower = debouncedSearchVal.toLowerCase().trim();
            const searchTerms = searchLower.split(/\s+/).filter(term => term.length > 0);
            
            // If multiple search terms, all must match (AND logic)
            if (searchTerms.length === 0) return true;
            
            // Build searchable text from all relevant fields
            const eventTitle = (req.eventId?.title || "Unknown Event").toLowerCase();
            const fullname = (req.fullname || "").toLowerCase();
            const srcode = (req.srcode || "").toLowerCase();
            const collegeDept = (req.collegeDept || "").toLowerCase();
            const email = (req.email || "").toLowerCase();
            const campus = (req.campus || "").toLowerCase();
            const yrlevelprogram = (req.yrlevelprogram || "").toLowerCase();
            const address = (req.address || "").toLowerCase();
            const contactNum = (req.contactNum || "").toLowerCase();
            const eventType = (req.type || "").toLowerCase();
            
            // Combine all searchable fields
            const searchableText = `${eventTitle} ${fullname} ${srcode} ${collegeDept} ${email} ${campus} ${yrlevelprogram} ${address} ${contactNum} ${eventType}`;
            
            // Check if all search terms are found in the searchable text
            return searchTerms.every(term => searchableText.includes(term));
          });
      
      console.log("After search filter:", afterSearchFilter.length, "requirements");
      
      const afterStatusFilter = afterSearchFilter
          .filter((req) => {
            if (searchStatus === 3) return true; // Show all
            if (searchStatus === 2) {
              // Show not evaluated (null or undefined)
              return req.accepted === null || req.accepted === undefined;
            }
            // Show specific status (0 = rejected, 1 = approved)
            return req.accepted === searchStatus;
          });
      
      console.log("After status filter:", afterStatusFilter.length, "requirements");

      const filteredAndMappedData = afterStatusFilter
          .map((req) => [
            req.eventId?.title || "Unknown Event",
            req.fullname || "N/A",
            req.accepted === 0
              ? chipMap.rejected
              : req.accepted === 1
              ? chipMap.approved
              : chipMap.notEvaluated,
            typeof req.accepted !== "number" ? (
              <MenuButtonTemplate
                items={[
                  {
                    label: "View Requirement",
                    icon: <RemoveRedEyeIcon />,
                    onClick: () => {
                      setSelectedFormData(req);
                      setFormData(req);
                      setViewFormData(true);
                    },
                  },
                  {
                    label: "Accept",
                    icon: <ThumbUpIcon />,
                    onClick: () => {
                      acceptRequirement(req.id)
                        .then(() => {
                          showSnackbarMessage(
                            "Successfully accepted requirement",
                            "success"
                          );
                        })
                        .catch(() => {
                          showSnackbarMessage(
                            "An error occured in accepting requirement",
                            "error"
                          );
                        })
                        .finally(() => {
                          setForceRefresh(forceRefresh + 1);
                        });
                    },
                  },
                  {
                    label: "Reject",
                    icon: <ThumbDownIcon />,
                    onClick: () => {
                      rejectRequirement(req.id)
                        .then(() => {
                          showSnackbarMessage(
                            "Successfully rejected requirement"
                          );
                        })
                        .catch(() => {
                          showSnackbarMessage(
                            "An error occured in rejecting requirement"
                          );
                        })
                        .finally(() => {
                          setForceRefresh(forceRefresh + 1);
                        });
                    },
                  },
                ]}
              />
            ) : (
              <MenuButtonTemplate
                items={[
                  {
                    label: "View Requirement",
                    icon: <RemoveRedEyeIcon />,
                    onClick: () => {
                      setSelectedFormData(req);
                      setFormData(req);
                      setViewFormData(true);
                    },
                  },
                  {
                    label: "Show Evaluation Form",
                    icon: <InsertDriveFileIcon />,
                    onClick: () => {
                      navigate(`/evaluation/${req.id}`);
                    },
                  },
                ]}
              />
              // <IconButton
              //   onClick={() => {
              //     setSelectedFormData(req);
              //     setFormData(req);
              //     setViewFormData(true);
              //   }}
              // >
              //   <RemoveRedEyeIcon />
              // </IconButton>
            ),
          ]);

      console.log("✅ Final processed table data:", filteredAndMappedData.length, "rows");
      
      if (filteredAndMappedData.length === 0 && requirementsData.length > 0) {
        console.warn("⚠️ All requirements filtered out!");
        console.warn("Total requirements:", requirementsData.length);
        console.warn("After search filter:", afterSearchFilter.length);
        console.warn("After status filter:", afterStatusFilter.length);
        console.warn("Search status:", searchStatus);
        console.warn("Search value:", searchVal);
      }
      
      setTableData(filteredAndMappedData);
      setLoading(false);
      })
      .catch((err) => {
        console.error("❌ Error fetching requirements:", err);
        console.error("Error details:", err.response?.data || err.message);
        console.error("Error stack:", err.stack);
        console.error("Error status:", err.response?.status);
        
        // Check if it's an authentication error
        if (err.response?.status === 403) {
          const errorMessage = err.response?.data?.message || "Unauthorized";
          console.error("⚠️ Authentication error - user may not be logged in or token expired");
          console.error("Token in localStorage:", !!localStorage.getItem("token"));
          
          // Show user-friendly error message
          if (errorMessage.includes("Unauthorized") || errorMessage.includes("Token")) {
            showSnackbarMessage(
              "Please log in to view requirements. Your session may have expired.",
              "error"
            );
            // Optionally redirect to login after a delay
            setTimeout(() => {
              navigate("/login");
            }, 2000);
          } else {
            showSnackbarMessage(
              `Access denied: ${errorMessage}`,
              "error"
            );
          }
        } else {
          showSnackbarMessage(
            `An error occurred while fetching requirements: ${err.message || "Unknown error"}`,
            "error"
          );
        }
        
        setTableData([]);
        setLoading(false);
      });
  }, [forceRefresh, debouncedSearchVal, searchStatus, showSnackbarMessage, setFormData]);

  const ModRightComponents = [
    <CustomDropdown
      key="filter-status-dropdown"
      label="Filter Status"
      width="200px"
      menu={[
        { key: "All", value: 3 },
        { key: "Not Evaluated", value: 2 },
        { key: "Approved", value: 1 },
        { key: "Rejected", value: 0 },
      ]}
      onChange={(event) => {
        setSearchStatus(parseInt(event.target.value));
      }}
    />,
  ];

  if (loading) {
    return (
      <PageLayout page="requirement-evaluation">
        <TextHeader>REQUIREMENT EVALUATION</TextHeader>
        <TextSubHeader>Evaluate participant requirements here</TextSubHeader>
        <LoadingSpinner message="Loading requirements..." />
      </PageLayout>
    );
  }

  return (
    <>
      <RequirementForm
        preventLoadingCache
        viewOnly
        eventId={selectedFormData.eventId?.id || selectedFormData.eventId || 0}
        eventType={selectedFormData.type || "external"}
        open={viewFormData}
        setOpen={setViewFormData}
      />
      <PageLayout page="requirement-evaluation">
        <TextHeader>REQUIREMENT EVALUATION</TextHeader>
        <TextSubHeader>Evaluate participant requirements here</TextSubHeader>
        {tableData.length === 0 ? (
          <div style={{ 
            padding: "40px", 
            textAlign: "center",
            color: "var(--text-landing, #666)"
          }}>
            <Typography variant="h6" style={{ marginBottom: "10px" }}>
              No requirements found
            </Typography>
            <Typography variant="body2" style={{ marginBottom: "20px" }}>
              {debouncedSearchVal || searchStatus !== 3
                ? "Try adjusting your search or filter criteria"
                : "No requirements have been submitted yet"}
            </Typography>
            {debouncedSearchVal && (
              <Typography variant="caption" style={{ 
                display: "block",
                marginTop: "10px",
                color: "#999",
                fontSize: "0.85rem"
              }}>
                Search: "{debouncedSearchVal}"
              </Typography>
            )}
          </div>
        ) : (
          <>
            {(debouncedSearchVal || searchStatus !== 3) && (
              <Box sx={{ 
                padding: "10px 20px", 
                backgroundColor: "#f5f5f5", 
                borderRadius: "8px",
                marginBottom: "10px",
                display: "flex",
                alignItems: "center",
                gap: 1
              }}>
                <Typography variant="body2" color="text.secondary">
                  Showing {tableData.length} result{tableData.length !== 1 ? 's' : ''}
                  {debouncedSearchVal && ` for "${debouncedSearchVal}"`}
                  {searchStatus !== 3 && ` (${searchStatus === 2 ? 'Not Evaluated' : searchStatus === 1 ? 'Approved' : 'Rejected'})`}
                </Typography>
              </Box>
            )}
            <DataTable
              title="Participant Requirements"
              fields={["Event Title", "Participant Name", "Status", "Actions"]}
              data={tableData}
              onSearch={(key) => setSearchVal(key)}
              componentBeforeSearch={ModRightComponents}
              // componentOnLeft={ModLeftComponents}
            />
          </>
        )}
      </PageLayout>
    </>
  );
};

export default RequirementEvalPage;
