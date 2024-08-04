import { Button, Typography, AppBar, Toolbar } from "@mui/material";
import { useNavigate, useSearchParams } from "@remix-run/react";
import { HighlightOffRounded as HighlightOffRoundedIcon } from "@mui/icons-material";
import { FlexContainer } from "~/components/FlexContainer";

export default function PresentationFail() {
  const navigate = useNavigate();

  const [params] = useSearchParams();

  const errorMessage = params.get("error") ?? "Unknown Error";

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <Typography
            variant="h4"
            component="h1"
            id="presentation-failed-title"
          >
            Presentation Failed
          </Typography>
        </Toolbar>
      </AppBar>
      <FlexContainer
        component="main"
        maxWidth="xl"
        disableGutters
        sx={{ justifyContent: "space-evenly" }}
      >
        <Typography variant="h3" component="h2">
          The Verifier has declined your credentials
        </Typography>
        <Typography>Reason: {errorMessage}</Typography>
        <HighlightOffRoundedIcon color="error" sx={{ fontSize: "200px" }} />
        <Button onClick={() => navigate("/credentials")}>Back</Button>
      </FlexContainer>
    </>
  );
}
