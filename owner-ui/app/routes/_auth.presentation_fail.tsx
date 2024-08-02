import { Button, Typography, AppBar, Toolbar, SvgIcon } from "@mui/material";
import { useNavigate } from "@remix-run/react";
import HighlightOffRoundedIcon from "@mui/icons-material/HighlightOffRounded";

export default function PresentationFail() {
  const navigate = useNavigate();

  function getQueryParam(param: string) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  }

  const errorMessage = getQueryParam("error");

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
            Presentation Fail
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
          The Verifier has declined your credentials because of {errorMessage}
        </Typography>
        <SvgIcon
          color="error"
          component={HighlightOffRoundedIcon}
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
