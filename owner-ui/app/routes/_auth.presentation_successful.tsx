import { Button, Typography, AppBar, Toolbar, SvgIcon } from "@mui/material";
import { useNavigate } from "@remix-run/react";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";

export default function PresentationSuccess() {
  const navigate = useNavigate();

  return (
    <>
      <AppBar position="sticky">
        <Toolbar
          sx={{
            pb: 2,
            pt: 1,
            minHeight: 128,
            alignItems: "flex-end",
            text_align: "center",
            justifyContent: "center",
          }}
        >
          <Typography variant="h1" component="h2" gutterBottom>
            Presentation Successful
          </Typography>
        </Toolbar>
      </AppBar>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "space-evenly",
          height: "calc(100vh - 328px)", // Subtract the AppBar height
          textAlign: "center",
        }}
      >
        <Typography variant="h3" gutterBottom>
          The Verifier has approved your credentials
        </Typography>
        <SvgIcon
          color="success"
          component={CheckCircleOutlineRoundedIcon}
          sx={{ fontSize: 200 }}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate("/credentials")}
        >
          Back
        </Button>
      </div>
    </>
  );
}
