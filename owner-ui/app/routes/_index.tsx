import { LoaderFunctionArgs, redirect } from "@remix-run/node";
import { isRouteErrorResponse } from "@remix-run/react";
import type { MetaFunction } from "@remix-run/react";
import { getSessionFromRequest, destroySession, walletBackendClient, authHeaders } from "~/utils";

export async function loader({ request }: LoaderFunctionArgs) {
  // Check the user's session token and redirect them as needed.
  const session = await getSessionFromRequest(request);
  if (session.get("token")) {
    try {
      await walletBackendClient.get("/session",
        {
          headers: authHeaders(session)
        }
      );
    } catch {
      await walletBackendClient.get("/logout");
        return redirect("/login", {
          headers: {
            "Set-Cookie": await destroySession(session),
          },
        });
    }
  }
  await walletBackendClient.get("/logout");
  return redirect("/login", {
    headers: {
      "Set-Cookie": await destroySession(session),
    },
  });
}

export const meta: MetaFunction = ({ error }) => {
  let title = "SSI Wallet";
  if (error) {
    title = isRouteErrorResponse(error)
      ? `${error.status} ${error.statusText}`
      : "Error!";
  }
  return [
    { title: title },
    { name: "description", content: "Take control of your identity." },
  ];
};

export default function Index() {
  return <></>;
}
