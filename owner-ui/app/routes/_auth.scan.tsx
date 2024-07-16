import { AddLink as AddLinkIcon } from "@mui/icons-material";
import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { isRouteErrorResponse, type MetaFunction } from "@remix-run/react";
import { type IDetectedBarcode, Scanner } from "@yudiel/react-qr-scanner";
import { FlexContainer } from "~/components/FlexContainer";

export const meta: MetaFunction = ({ error }) => {
  let title = "Scan QR Code - SSI Wallet";
  if (error) {
    title = isRouteErrorResponse(error)
      ? `${error.status} ${error.statusText}`
      : "Error!";
  }
  return [
    {
      title: title,
    },
    { name: "description", content: "View and manage credentials" },
  ];
};

// TODO: error handling
async function handleScan(result: IDetectedBarcode[]) {
  const scan = result[0];
  const resp = await fetch(
    `https://owner-lib:8081/presentation/init?${scan.rawValue}`,
    {
      method: "GET",
    },
  );
  console.log(resp);
}

export default function Scan() {
  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <Typography
            variant="h4"
            component="h1"
            id="credentials-appbar-title"
            flexGrow={1}
          >
            Scan QR code
          </Typography>
          <Tooltip id="enter-link-tooltip" title="Type Credential link">
            <IconButton color="inherit" aria-label="Type Credential link">
              <AddLinkIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl" disableGutters>
        <Box
          sx={{
            width: "fit-content",
            height: "fit-content",
          }}
        >
          <Scanner
            styles={{
              finderBorder: 50,
            }}
            onScan={handleScan}
          />
        </Box>
      </FlexContainer>
    </>
  );
}
