import { Box, Typography } from "@mui/material";
import ArrowCircleRightIcon from "@mui/icons-material/ArrowCircleRight";
import LandingHeader from "../components/Headers/LandingHeader";
import FlexBox from "../components/FlexBox";
import CustomButton from "../components/Buttons/CustomButton";
import CustomDivider from "../components/Divider/CustomDivider";
import MediaCard from "../components/Cards/MediaCard";
import HorizontalCarousel from "../components/Carousel/HorizontalCarousel";
import Footer from "../components/Footers/Footer";
import { useContext, useEffect, useState } from "react";
import MembershipAppForm from "../components/Forms/MembershipAppForm";
import ConfirmModal from "../components/Modal/ConfirmModal";
import RequirementForm from "../components/Forms/RequirementForm";
import { getAllPublicEvents } from "../api/events";
import {
  ExternalEventProposalType,
  InternalEventProposalType,
} from "../interface/types";
import TextHeader from "../components/Headers/TextHeader";
import { FormDataContext } from "../contexts/FormDataProvider";
import FormPreviewDetails from "../components/Forms/FormPreviewDetails";
import DataPrivacy from "../components/Popups/DataPrivacy";
import { useMediaQuery } from "react-responsive";
import NewsThumbnailCarousel from "../components/NewsThumbnailCarousel";
import { useNavigate } from "react-router-dom";
import { People, Assignment } from "@mui/icons-material";
import { SnackbarContext } from "../contexts/SnackbarProvider";
import { getImagePath } from "../utils/imagePath";

const Landing = () => {
  const { setFormData } = useContext(FormDataContext);
  const navigate = useNavigate();
  const { showSnackbarMessage } = useContext(SnackbarContext);

  const [openVolunteerForm, setOpenVolunteerForm] = useState(false);
  const [openRequirementForm, setOpenRequirementForm] = useState(false);
  const [publicEvents, setPublicEvents] = useState<any[]>([]);

  const [openDataPrivacy, setOpenDataPrivacy] = useState(false);
  const [openPreview, setOpenPreview] = useState(false);
  const [previewData, setPreviewData] = useState<any>({});

  const [openConfirm, setOpenConfirm] = useState(false);
  const [eventType] = useState<"external" | "internal">(
    "external"
  );
  const [selectedEventId] = useState<number | undefined>(
    undefined
  );

  const isMobile = useMediaQuery({
    query: "(max-width: 600px)",
  });

  

  const viewDataCallback = (eventData: any) => {
    return () => {
      setPreviewData(eventData);
      setOpenPreview(true);
    };
  };

  useEffect(() => {
    getAllPublicEvents().then((response) => {
      const externalEvents: ExternalEventProposalType[] =
        response.data.external;
      const internalEvents: InternalEventProposalType[] =
        response.data.internal;

      setPublicEvents([...externalEvents, ...internalEvents]);
    });
  }, []);

  return (
    <Box>
      {/* <FormDataLoaderModal
        hidePrintButton
        data={previewData}
        formType={previewType}
        open={openPreview}
        setOpen={setOpenPreview}
      /> */}
      <FormPreviewDetails
        open={openPreview}
        eventData={previewData}
        setOpen={setOpenPreview}
      />
      <MembershipAppForm
        eventId={selectedEventId}
        open={openVolunteerForm}
        setOpen={setOpenVolunteerForm}
        onSubmit={() => {
          setFormData({});
          setOpenRequirementForm(true);
        }}
      />
      <DataPrivacy open={openDataPrivacy} setOpen={setOpenDataPrivacy} />
      {selectedEventId && (
        <>
          <RequirementForm
            preventLoadingCache
            eventId={selectedEventId}
            open={openRequirementForm}
            eventType={eventType}
            setOpen={setOpenRequirementForm}
            afterOpen={() => {
              setFormData({});
            }}
          />
        </>
      )}
      <ConfirmModal
        message="Do you want to apply for a membership before volunteering?"
        open={openConfirm}
        setOpen={setOpenConfirm}
        onAccept={() => {
          setFormData({});
          setOpenVolunteerForm(true);
          setOpenDataPrivacy(true);
        }}
        onCancel={() => {
          setOpenDataPrivacy(true);
          setOpenRequirementForm(true);
        }}
      />
      <LandingHeader
        setOpenMembership={(state) => {
          setOpenDataPrivacy(true);
          setOpenVolunteerForm(state);
        }}
      />
      <Box
        id="home"
        height="90vh"
        width="100%"
        sx={{
          backgroundImage: `url('${getImagePath('/images/landing-bg.png')}')`,
          backgroundRepeat: "no-repeat",
          backgroundSize: "cover",
        }}
      >
        <FlexBox
          height="100%"
          width={isMobile ? "calc(100% - 10px)" : "calc(50% - 40px)"}
          alignItems="center"
          justifyContent="center"
          paddingLeft={isMobile ? "10px" : "40px"}
          flexDirection="column"
        >
          <Box>
            <Typography
              width="100%"
              variant={isMobile ? "h4" : "h2"}
              fontWeight="bold"
              fontFamily="Inter"
              color="var(--text-landing)"
              gutterBottom
            >
              Sulambi Volunteer Organization Students Auxillary
            </Typography>
          </Box>
          <FlexBox justifyContent="flex-start" width="100%" gap="15px" flexWrap="wrap">
            <CustomButton
              label="Get Started"
              variant="contained"
              endIcon={<ArrowCircleRightIcon />}
              sx={{
                backgroundColor: "var(--text-landing)",
                color: "white",
                padding: "10px 20px",
              }}
              hoverSx={{
                color: "black",
                backgroundColor: "white",
              }}
              onClick={() => {
                window.location.href = "#events";
              }}
            />
          </FlexBox>
        </FlexBox>
      </Box>
      <Box height="90vh" width="100%" paddingTop="200px" id="events">
        <Typography
          width={isMobile ? "100%" : "50%"}
          margin="0 auto"
          variant={isMobile ? "h5" : "h4"}
          color="var(--text-landing)"
          textAlign="center"
          gutterBottom
        >
          Bolunterismo ang boses ng kabataan nais kumilos para sa kanyang
          komunidad
        </Typography>
        <CustomDivider
          width={isMobile ? "95%" : "50%"}
          thickness="2px"
          color="var(--divider-color)"
          mt="20px"
        />
        <FlexBox
          margin="auto"
          marginTop="50px"
          width={isMobile ? "95vw" : "70vw"}
          justifyContent="center"
          flexWrap="wrap"
          gap="2em"
        >
          {publicEvents.length === 0 && (
            <TextHeader sx={{ color: "gray" }}>(No current events)</TextHeader>
          )}
          {publicEvents.length > 0 &&
          ((isMobile && publicEvents.length >= 2) ||
            publicEvents.length > 4) ? (
            <HorizontalCarousel>
              {publicEvents.map((event, id) => (
                <MediaCard
                  key={id}
                  width={isMobile ? "73vw" : "20vw"}
                  cardTitle={event.title}
                  location={event.location ?? event.venue ?? ""}
                  onViewDetails={viewDataCallback(event)}
                />
              ))}
            </HorizontalCarousel>
          ) : (
            publicEvents.map((event) => (
              <MediaCard
                width={isMobile ? "auto" : "20vw"}
                cardTitle={event.title}
                location={event.location ?? event.venue ?? ""}
                onViewDetails={viewDataCallback(event)}
              />
            ))
          )}
        </FlexBox>
      </Box>
      
      {/* News / Latest Reports Section */}
      <Box width="100%" paddingTop="40px" paddingBottom="80px">
        <Box width={isMobile ? "95vw" : "70vw"} margin="0 auto">
          <NewsThumbnailCarousel title="Latest News" limit={6} />
        </Box>
      </Box>
      
      {/* Evaluation Forms Section */}
      <Box height="90vh" width="100%" paddingTop="200px" id="evaluations">
        <Typography
          width={isMobile ? "100%" : "50%"}
          margin="0 auto"
          variant={isMobile ? "h5" : "h4"}
          color="var(--text-landing)"
          textAlign="center"
          gutterBottom
        >
          Share Your Experience - Help Us Improve
        </Typography>
        <CustomDivider
          width={isMobile ? "95%" : "50%"}
          thickness="2px"
          color="var(--divider-color)"
          mt="20px"
        />
        <FlexBox
          margin="auto"
          marginTop="50px"
          width={isMobile ? "95vw" : "70vw"}
          justifyContent="center"
          flexWrap="wrap"
          gap="2em"
        >
          {/* Beneficiary Evaluation Card */}
          <Box
            sx={{
              width: isMobile ? "100%" : "300px",
              backgroundColor: "white",
              borderRadius: "15px",
              padding: "30px",
              boxShadow: "0 8px 25px rgba(0, 0, 0, 0.10)",
              border: "1px solid var(--divider-color)",
              cursor: "pointer",
              transition: "all 0.3s ease",
              "&:hover": {
                transform: "translateY(-5px)",
                boxShadow: "0 12px 35px rgba(0, 0, 0, 0.15)",
              },
            }}
            onClick={() => navigate('/beneficiary-evaluation')}
          >
            <FlexBox alignItems="center" gap="15px" mb="20px">
              <People sx={{ fontSize: 40, color: "var(--text-landing)" }} />
              <Box>
                <Typography variant="h6" component="h3" sx={{ fontWeight: "bold", color: "var(--text-landing)" }}>
                  Beneficiary Evaluation
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  I received services/benefits
                </Typography>
              </Box>
            </FlexBox>
            
            <Typography variant="body2" paragraph>
              Evaluate the service you received including quality, volunteer 
              helpfulness, and community impact.
            </Typography>
            
            <FlexBox gap={1} flexWrap="wrap" mb="20px">
              <Box sx={{ 
                backgroundColor: "#f5f5f5", 
                color: "var(--text-default)", 
                padding: "4px 8px", 
                borderRadius: "12px", 
                fontSize: "0.75rem",
                fontWeight: "medium"
              }}>
                Service Quality
              </Box>
              <Box sx={{ 
                backgroundColor: "#f5f5f5", 
                color: "var(--text-default)", 
                padding: "4px 8px", 
                borderRadius: "12px", 
                fontSize: "0.75rem",
                fontWeight: "medium"
              }}>
                Community Impact
              </Box>
            </FlexBox>
            
            <CustomButton
              label="Start Beneficiary Evaluation"
              startIcon={<Assignment />}
              fullWidth
              sx={{
                backgroundColor: "var(--text-landing)",
                color: "white",
                "&:hover": { backgroundColor: "white", color: "black" }
              }}
            />
          </Box>
        </FlexBox>
      </Box>
      {/* <Box height="90vh" width="100%" paddingTop="200px" id="helpdesk">
        <Typography
          width="50%"
          margin="0 auto"
          variant="h4"
          color="var(--text-landing)"
          textAlign="center"
          gutterBottom
        >
          Maki-isa tayo tulungan ang nangangailangan.
        </Typography>
        <CustomDivider
          width="50%"
          thickness="2px"
          color="var(--divider-color)"
          mt="20px"
        />
        <FlexBox
          margin="auto"
          marginTop="50px"
          width="70vw"
          justifyContent="center"
          flexWrap="wrap"
          gap="2em"
        >
          <TextHeader sx={{ color: "gray" }}>Soon</TextHeader>
        </FlexBox>
        <FlexBox
          margin="auto"
          marginTop="50px"
          width="70vw"
          justifyContent="center"
          flexWrap="wrap"
        >
          <HorizontalCarousel>
            <MediaCard />
            <MediaCard />
            <MediaCard />
            <MediaCard />
          </HorizontalCarousel>
        </FlexBox>
      </Box> */}
      
      <Footer />
    </Box>
  );
};

export default Landing;
