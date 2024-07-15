import {
  AccountBalanceWallet as AccountBalanceWalletIcon,
  Add as AddIcon,
  Logout as LogoutIcon,
  QrCode as QrCodeIcon,
} from "@mui/icons-material";
import {
  Typography,
  Unstable_Grid2 as Grid,
  AppBar,
  Toolbar,
  Tooltip,
  IconButton,
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  useScrollTrigger,
  Slide,
  SlideProps,
} from "@mui/material";
import type { LoaderFunction } from "@remix-run/node";
import {
  isRouteErrorResponse,
  json,
  useLoaderData,
  type MetaFunction,
} from "@remix-run/react";
import { useState } from "react";
import { CredentialCard } from "~/components/CredentialCard";
import { CredentialsGridContainer } from "~/components/CredentialsGridContainer";
import { FlexContainer } from "~/components/FlexContainer";

export const meta: MetaFunction = ({ error }) => {
  let title = "Credentials - SSI Wallet";
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

interface CredentialDataField {
  id: string;
  type: string;
  issuer_name: string | null;
  token: string | null;
}

export const loader: LoaderFunction = async () => {
  const resp = await fetch(
    `https://owner-lib:${process.env.CS3900_OWNER_AGENT_PORT}/credentials`,
    { method: "GET" },
  );
  const data: Array<CredentialDataField> = await resp.json();
  return json(data);
};

function HideOnScroll({ children }: Readonly<SlideProps>) {
  const trigger = useScrollTrigger();

  return (
    <Slide appear={false} direction="up" in={!trigger}>
      {children}
    </Slide>
  );
}

export default function Credentials() {
  const credentials: Array<CredentialDataField> = useLoaderData();
  const [value, setValue] = useState(0);

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
            Credentials
          </Typography>
          <Tooltip id="add-credential-tooltip" title="Add new credential">
            <IconButton color="inherit" aria-label="Add new credential">
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl" disableGutters={true}>
        <CredentialsGridContainer>
          <Grid
            container
            columns={{ xs: 4, sm: 8, md: 12 }}
            spacing={{ xs: 2, sm: 3 }}
            sx={{ mt: { xs: 1, md: 1.5 } }}
          >
            {credentials.map((credential) => {
              return (
                <Grid
                  key={credential.id}
                  sx={{ display: "flex" }}
                  justifyContent={"center"}
                  size={4}
                >
                  <CredentialCard credential={credential} />
                </Grid>
              );
            })}
          </Grid>
        </CredentialsGridContainer>
      </FlexContainer>
      <HideOnScroll>
        <Paper
          elevation={8}
          sx={{ position: "fixed", bottom: 0, left: 0, right: 0 }}
        >
          <BottomNavigation
            showLabels
            component="nav"
            value={value}
            onChange={(_event, newValue) => setValue(newValue)}
          >
            <BottomNavigationAction
              label="Wallet"
              icon={<AccountBalanceWalletIcon />}
            />
            <BottomNavigationAction label="Scan QR" icon={<QrCodeIcon />} />
            <BottomNavigationAction label="Logout" icon={<LogoutIcon />} />
          </BottomNavigation>
        </Paper>
      </HideOnScroll>
    </>
  );
}
