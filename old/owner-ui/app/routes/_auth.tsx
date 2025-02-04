import {
  AccountBalanceWallet as AccountBalanceWalletIcon,
  Logout as LogoutIcon,
  QrCode as QrCodeIcon,
} from "@mui/icons-material";
import {
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  Slide,
  type SlideProps,
  useScrollTrigger,
} from "@mui/material";
import { LoaderFunctionArgs } from "@remix-run/node";
import { Link, Outlet, redirect, useMatches } from "@remix-run/react";
import { useState } from "react";
import {
  authHeaders,
  destroySession,
  getSessionFromRequest,
  walletBackendClient,
} from "~/utils";

export async function loader({ request }: LoaderFunctionArgs) {
  // Check the user's session token and redirect them as needed.
  const session = await getSessionFromRequest(request);

  if (!session.get("token")) {
    await walletBackendClient.get("/logout");
    return redirect("/login", {
      headers: {
        "Set-Cookie": await destroySession(session),
      },
    });
  }
  try {
    await walletBackendClient.get("/session", {
      headers: authHeaders(session),
    });
    return null;
  } catch {
    await walletBackendClient.get("/logout");
    return redirect("/login", {
      headers: {
        "Set-Cookie": await destroySession(session),
      },
    });
  }
}

function HideOnScroll({ children }: Readonly<SlideProps>) {
  const trigger = useScrollTrigger();

  return (
    <Slide appear={false} direction="up" in={!trigger}>
      {children}
    </Slide>
  );
}

export default function Auth() {
  const matches = useMatches();
  const [value, setValue] = useState(
    ["/scan", "/present"].includes(matches.at(-1)?.pathname ?? "") ? 1 : 0,
  );

  return (
    <>
      <Outlet context={setValue} />
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
              component={Link}
              to="/credentials"
            />
            <BottomNavigationAction
              label="Scan QR"
              icon={<QrCodeIcon />}
              component={Link}
              to="/scan"
            />
            <BottomNavigationAction
              label="Logout"
              icon={<LogoutIcon />}
              component={Link}
              to="/logout"
            />
          </BottomNavigation>
        </Paper>
      </HideOnScroll>
    </>
  );
}
