import { Box, Typography } from "@mui/material";
import FlexBox from "../components/FlexBox";
import CustomButton from "../components/Buttons/CustomButton";

import EventIcon from "@mui/icons-material/Event";
import HistoryIcon from "@mui/icons-material/History";
import NewspaperIcon from "@mui/icons-material/Newspaper";
import VolunteerActivismIcon from "@mui/icons-material/VolunteerActivism";
// import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import SpaceDashboardIcon from "@mui/icons-material/SpaceDashboard";
import ConfirmModal from "../components/Modal/ConfirmModal";

import FactCheckIcon from "@mui/icons-material/FactCheck";
import ChecklistRtlIcon from "@mui/icons-material/ChecklistRtl";
// import FavoriteIcon from "@mui/icons-material/Favorite";
import PeopleAltIcon from "@mui/icons-material/PeopleAlt";

import { ReactNode, useContext, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { AccountDetailsContext } from "../contexts/AccountDetailsProvider";
import { logout } from "../api/auth";
import { SnackbarContext } from "../contexts/SnackbarProvider";
import QrCodeIcon from "@mui/icons-material/QrCode";
import { getImagePath } from "../utils/imagePath";

interface Props {
  page: string;
  children?: ReactNode;
}

const defaultSx = {
  borderRadius: "50px",
  padding: "10px 0px",
};

const sx = {
  ...defaultSx,
  paddingLeft: "20%",
};

const activeSx = {
  backgroundColor: "white",
};

const hoverSx = {
  backgroundColor: "#ffffffa8",
};

const style = { justifyContent: "flex-start" };

const PageLayout: React.FC<Props> = ({ page, children }) => {
  const [openLogoutDialog, setOpenLogoutDialog] = useState(false);
  const { accountDetails } = useContext(AccountDetailsContext);
  const { showSnackbarMessage } = useContext(SnackbarContext);

  const navigate = useNavigate();
  const location = useLocation();
  
  // Helper function to navigate only if not already on the target route
  const navigateIfDifferent = (path: string) => {
    if (location.pathname !== path) {
      navigate(path);
    }
  };

  return (
    <>
      <ConfirmModal
        title="Logout account"
        message="Are you sure you want to logout?"
        declineText="Cancel"
        open={openLogoutDialog}
        setOpen={setOpenLogoutDialog}
        onAccept={() => {
          const usertoken = localStorage.getItem("token");
          if (usertoken !== null) {
            logout(usertoken)
              .then(() => {
                showSnackbarMessage("Successfully logged out");
              })
              .finally(() => {
                localStorage.removeItem("token");
                localStorage.removeItem("membershipCache");
              });
          }
          navigate("/");
        }}
      />
      <FlexBox
        width="100%"
        height="100vh"
        justifyContent="center"
        alignItems="center"
        position="fixed"
        sx={{ top: 0, left: 0, right: 0, bottom: 0, overflow: "hidden" }}
      >
        <FlexBox
          flex="15"
          height="calc(100vh - 40px)"
          alignItems="center"
          padding="20px 10px"
          flexDirection="column"
          rowGap="15px"
          sx={{
            background: "linear-gradient(180deg, #C07F00 0%, #FFD95A 100%)",
            borderTopRightRadius: "20px",
            borderBottomRightRadius: "20px",
            boxShadow: "2px 0px 15px 0px #b3b3b3",
            overflowY: "auto",
          }}
        >
          <img
            src={getImagePath("/images/logo.png")}
            height="150px"
            width="150px"
            onClick={() => {
              navigate("/");
            }}
            style={{
              backgroundColor: "var(--body-color)",
              borderRadius: "50%",
              cursor: "pointer",
            }}
          />
          <Typography
            variant="h6"
            fontWeight="bold"
            color="var(--text-default)"
            textAlign="center"
          >
            {`Welcome back ${localStorage.getItem("username") ?? "User"}!`}
          </Typography>
          <FlexBox
            width="100%"
            height="100%"
            flexDirection="column"
            justifyContent="flex-start"
          >
            {accountDetails.accountType === "admin" && (
              <FlexBox
                marginTop="30px"
                width="100%"
                flexDirection="column"
                rowGap="30px"
              >
                <CustomButton
                  fullWidth
                  label="Dashboard"
                  startIcon={<SpaceDashboardIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "" || page === "dashboard"
                      ? { ...sx, ...activeSx }
                      : sx
                  }
                  onClick={() => navigateIfDifferent("/admin/dashboard")}
                />
                <CustomButton
                  fullWidth
                  label="Event Approval"
                  startIcon={<VolunteerActivismIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={page === "event-approval" ? { ...sx, ...activeSx } : sx}
                  onClick={() => navigateIfDifferent("/admin/event-approval")}
                />
                {/* <CustomButton
                  fullWidth
                  label="Calendar"
                  startIcon={<CalendarMonthIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={page === "calendar" ? { ...sx, ...activeSx } : sx}
                  onClick={() => navigate("/admin/calendar")}
                /> */}
                <CustomButton
                  fullWidth
                  label="Report"
                  startIcon={<NewspaperIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={page === "report" ? { ...sx, ...activeSx } : sx}
                  onClick={() => navigateIfDifferent("/admin/report")}
                />
                <CustomButton
                  fullWidth
                  label="Accounts"
                  startIcon={<PeopleAltIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={page === "accounts" ? { ...sx, ...activeSx } : sx}
                  onClick={() => navigateIfDifferent("/admin/accounts")}
                />
              </FlexBox>
            )}
            {accountDetails.accountType === "officer" && (
              <FlexBox
                marginTop="30px"
                width="100%"
                flexDirection="column"
                rowGap="30px"
              >
                <CustomButton
                  fullWidth
                  label="Dashboard"
                  startIcon={<SpaceDashboardIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "" || page === "dashboard"
                      ? { ...sx, ...activeSx }
                      : sx
                  }
                  onClick={() => navigateIfDifferent("/officer/dashboard")}
                />
                <CustomButton
                  fullWidth
                  label="Event Proposal"
                  startIcon={<VolunteerActivismIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={page === "event-proposal" ? { ...sx, ...activeSx } : sx}
                  onClick={() => navigateIfDifferent("/officer/event-proposal")}
                />
                <CustomButton
                  fullWidth
                  label="Membership Approval"
                  startIcon={<ChecklistRtlIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "membership-approval" ? { ...sx, ...activeSx } : sx
                  }
                  onClick={() => navigateIfDifferent("/officer/membership-approval")}
                />
                <CustomButton
                  fullWidth
                  label="Requirement Evaluation"
                  startIcon={<FactCheckIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "requirement-evaluation"
                      ? { ...sx, ...activeSx }
                      : sx
                  }
                  onClick={() => navigateIfDifferent("/officer/requirement-evaluation")}
                />
              </FlexBox>
            )}
            {accountDetails.accountType === "member" && (
              <FlexBox
                marginTop="30px"
                width="100%"
                flexDirection="column"
                rowGap="30px"
              >
                <CustomButton
                  fullWidth
                  label="Events"
                  startIcon={<EventIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "" || page === "events"
                      ? { ...sx, ...activeSx }
                      : sx
                  }
                  onClick={() => navigateIfDifferent("/member/events")}
                />
                <CustomButton
                  fullWidth
                  label="Participation History"
                  startIcon={<HistoryIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "" || page === "participation"
                      ? { ...sx, ...activeSx }
                      : sx
                  }
                  onClick={() => navigateIfDifferent("/member/participation")}
                />
                <CustomButton
                  fullWidth
                  label="Share QrCode"
                  startIcon={<QrCodeIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={page === "qr" ? { ...sx, ...activeSx } : sx}
                  onClick={() => navigateIfDifferent("/member/qr-code-share")}
                />
                {/* <CustomButton
                  fullWidth
                  label="Helpdesk"
                  startIcon={<FavoriteIcon />}
                  style={style}
                  hoverSx={hoverSx}
                  sx={
                    page === "" || page === "helpdesk"
                      ? { ...sx, ...activeSx }
                      : sx
                  }
                  onClick={() => navigate("/member/helpdesk")}
                /> */}
              </FlexBox>
            )}
            <FlexBox 
              width="100%" 
              marginTop="30px"
              flexDirection="column"
              rowGap="30px"
            >
              <CustomButton
                fullWidth
                label="Logout"
                style={style}
                hoverSx={hoverSx}
                sx={sx}
                onClick={() => {
                  setOpenLogoutDialog(true);
                }}
              />
            </FlexBox>
          </FlexBox>
        </FlexBox>
        <Box
          flex="85"
          height="calc(100vh - 40px)"
          width="calc(100% - 40px)"
          padding="20px"
          sx={{ overflow: "auto" }}
        >
          {children}
        </Box>
      </FlexBox>
    </>
  );
};

export default PageLayout;
