import { LoaderFunctionArgs, redirect } from "@remix-run/node";
import { isRouteErrorResponse } from "@remix-run/react";
import type { MetaFunction } from "@remix-run/react";
import { authHeaderFromRequest } from "~/utils";

export async function loader({ request }: LoaderFunctionArgs) {
  try {
    await fetch(
      `https://owner-lib:${process.env.CS3900_OWNER_AGENT_PORT}/session`,
      { headers: await authHeaderFromRequest(request) },
    );
    return redirect("/credentials");
  } catch {
    return redirect("/login");
  }
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
