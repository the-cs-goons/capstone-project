import { Button, Typography, AppBar, Toolbar, IconButton} from "@mui/material";
import { Add as AddIcon } from "@mui/icons-material";
import { useNavigate, Link} from "@remix-run/react";

export default function PresentationSuccess() {
  const navigate = useNavigate();

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end", text_align: "center", justifyContent: "center"}}>
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
          justifyContent: "center",
          height: "calc(100vh - 328px)", // Subtract the AppBar height
          textAlign: "center"
        }}
      >
        <Typography variant="h3" gutterBottom>
          The Verifier has approved your credentials
        </Typography>
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
