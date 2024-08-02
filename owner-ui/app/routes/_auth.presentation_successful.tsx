import { Button, Typography, AppBar, Toolbar } from "@mui/material";
import { useNavigate } from "@remix-run/react";

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
          justifyContent: "start",
          height: "calc(100vh - 328px)", // Subtract the AppBar height
          textAlign: "center",
        }}
      >
        <Typography style={{ flex: "1" }} variant="h3" gutterBottom>
          The Verifier has approved your credentials
        </Typography>
        <svg style={{ flex: "4" }} width={400} height={400}>
          <circle
            fill="none"
            stroke="#68E534"
            strokeWidth={20}
            cx={200}
            cy={200}
            r={190}
          />
          <polyline
            fill="none"
            stroke="#68E534"
            strokeWidth={24}
            points="88,214 173,284 304,138"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
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
