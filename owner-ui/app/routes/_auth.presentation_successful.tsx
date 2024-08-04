import { Button, Typography, AppBar, Toolbar } from "@mui/material";
import { useNavigate } from "@remix-run/react";
import { CheckCircleOutlineRounded as CheckCircleOutlineRoundedIcon } from "@mui/icons-material";
import { FlexContainer } from "~/components/FlexContainer";

export default function PresentationSuccess() {
  const navigate = useNavigate();

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <Typography
            variant="h4"
            component="h1"
            id="presentation-successful-title"
          >
            Presentation Successful
          </Typography>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl" disableGutters>
        <Typography variant="h3" component="h2">
          The Verifier has approved your credentials
        </Typography>
        <CheckCircleOutlineRoundedIcon
          color="success"
          sx={{ fontSize: "200px" }}
        />
        <Button onClick={() => navigate("/credentials")}>Back</Button>
      </FlexContainer>
    </>
  );
}
