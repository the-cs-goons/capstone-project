import { Button, Typography, AppBar, Toolbar } from "@mui/material";
import { useNavigate } from "@remix-run/react";

export default function PresentationFail() {
  const navigate = useNavigate();

  function getQueryParam(param: string) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  }

  const errorMessage = getQueryParam('error');

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
          justifyContent: "center",
          height: "calc(100vh - 328px)", // Subtract the AppBar height
          textAlign: "center",
        }}
      >
        <Typography style={{flex: "1"}} variant="h3" gutterBottom>
          The Verifier has declined your credentials because of {errorMessage}
        </Typography>
        <svg style={{flex: "4"}} width={400} height={400}>
          <circle fill="none" stroke="red" strokeWidth={20} cx={200} cy={200} r={190}/>
          <line x1="46" y1="74" x2="361" y2="317" stroke="red" strokeWidth={24}/>
          <line x1="354" y1="74" x2="46" y2="326" stroke="red" strokeWidth={24}/>
        </svg>
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