import { Typography } from "@mui/material";
import { Outlet } from "@remix-run/react";
import { LoaderFunctionArgs, redirect } from "@remix-run/node";
import {
  authHeaderFromRequest,
  destroySession,
  getSession,
  walletBackendClient,
} from "~/utils";

export async function loader({ request }: LoaderFunctionArgs) {
  const auth = await authHeaderFromRequest(request);
  if (!auth) return null;
  try {
    await walletBackendClient.get("/session", { headers: auth });
    return redirect("/credentials");
  } catch {
    return await destroySession(
      await getSession(request.headers.get("Cookie")),
    );
  }
}

export default function Locked() {
  return (
    <>
      <Typography variant="h1">Wallet App</Typography>
      <Outlet />
    </>
  );
}
