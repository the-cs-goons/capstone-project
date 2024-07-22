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
import { Link, Outlet, useMatches } from "@remix-run/react";
import { useState } from "react";

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
  // TODO: make this work in individual credential screens
  const [value, setValue] = useState(
    matches.at(-1)?.pathname === "/credentials" ? 0 : 1,
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
            <BottomNavigationAction label="Logout" icon={<LogoutIcon />} />
          </BottomNavigation>
        </Paper>
      </HideOnScroll>
    </>
  );
}
