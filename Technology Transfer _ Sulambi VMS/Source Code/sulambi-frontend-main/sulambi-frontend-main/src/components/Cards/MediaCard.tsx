import { MediaCardProps } from "../../interface/props";
import {
  Card,
  CardActions,
  CardContent,
  CardMedia,
  Typography,
} from "@mui/material";
import CustomButton from "../Buttons/CustomButton";
import FlexBox from "../FlexBox";
import { useMediaQuery } from "react-responsive";
import { getImagePath } from "../../utils/imagePath";

const MediaCard: React.FC<MediaCardProps> = ({
  cardTitle,
  children,
  location,
  height,
  width,
  contentHeight,
  onViewDetails,
  onVolunteer,
}) => {
  const isMobile = useMediaQuery({
    query: "(max-width: 600px)",
  });

  return (
    <Card
      sx={{
        width: width,
        height: height ?? "50vh",
        cursor: "pointer",
        transition: ".5s",
        boxShadow: "0 0 10px 1px gray",
        border: "1px solid #e0e0e0",
        borderRadius: "10px",
        backgroundColor: "#fffbf3",
        color: "var(--text-landing)",
        ":hover": {
          transform: "translateY(-3px)",
          boxShadow: "0 0 25px 1px gray",
        },
      }}
    >
      <CardMedia
        component="img"
        image={getImagePath("/images/default-image.png")}
        title="default title"
        sx={{
          bgcolor: "black",
          height: "25vh",
          border: "2px solid #f0f0f0",
          borderRadius: "8px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          margin: "8px",
          width: "calc(100% - 16px)",
        }}
      />
      <CardContent sx={{ height: contentHeight ?? "27%" }}>
        <Typography gutterBottom variant="h6" fontWeight="bold" component="div">
          {cardTitle}
        </Typography>
        <Typography
          gutterBottom
          variant={isMobile ? "caption" : "body1"}
          // component="div"
          color="var(--text-landing-light)"
          textOverflow="ellipsis"
        >
          {location}
        </Typography>
        {children}
      </CardContent>
      <CardActions>
        <FlexBox justifyContent="flex-end" width="100%" gap="10px">
          {onVolunteer && (
            <CustomButton
              label="Join"
              variant="contained"
              disableElevation
              hoverSx={{
                color: "white",
                backgroundColor: "#2d3529",
              }}
              sx={{
                backgroundColor: "var(--text-landing)",
                border: "1px solid var(--text-landing)",
                borderRadius: "10px",
                padding: isMobile ? "5px" : undefined,
                fontSize: isMobile ? "9pt" : undefined,
                color: "white",
              }}
              onClick={onVolunteer}
            />
          )}
          <CustomButton
            label="View Details"
            variant="contained"
            disableElevation
            hoverSx={{
              color: "var(--text-landing)",
              backgroundColor: "white",
            }}
            sx={{
              backgroundColor: "var(--text-landing)",
              border: "1px solid var(--text-landing)",
              borderRadius: "10px",
              padding: isMobile ? "5px" : undefined,
              fontSize: isMobile ? "9pt" : undefined,
              color: "white",
            }}
            onClick={onViewDetails}
          />
        </FlexBox>
      </CardActions>
    </Card>
  );
};

export default MediaCard;
