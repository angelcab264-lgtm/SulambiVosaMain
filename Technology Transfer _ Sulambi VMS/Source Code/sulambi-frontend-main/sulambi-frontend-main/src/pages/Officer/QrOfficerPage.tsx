import { Box, Typography } from "@mui/material";
import TextHeader from "../../components/Headers/TextHeader";
import PageLayout from "../PageLayout";
import { QRCodeSVG } from "qrcode.react";
import FlexBox from "../../components/FlexBox";

const QrOfficerPage = () => {
  return (
    <PageLayout page="qr">
      <FlexBox justifyContent="center" alignItems="center" height="100%">
        <Box
          width={"30vw"}
          padding="20px"
          borderRadius="10px"
          boxShadow="0 0 10px 1px gray"
          marginTop="40px"
        >
          <Box textAlign="center" margin="30px 0px">
            <QRCodeSVG value={`${window.location.origin}/qr`} />
            <Typography
              variant="body2"
              sx={{ marginTop: 2, wordBreak: "break-all", color: "text.secondary" }}
            >
              {`${window.location.origin}/qr`}
            </Typography>
          </Box>
          <TextHeader textAlign="center">Evaluation QR Code</TextHeader>
        </Box>
      </FlexBox>
    </PageLayout>
  );
};

export default QrOfficerPage;
