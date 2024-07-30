import { Typography } from "@mui/material";
import { Outlet } from "@remix-run/react";

export default function Locked() {
  return (
    <>
      <Typography variant="h1">Wallet App</Typography>
      <Outlet />
    </>
  );
}
