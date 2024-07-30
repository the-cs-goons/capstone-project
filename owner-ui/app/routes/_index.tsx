import { LoaderFunctionArgs, redirect } from "@remix-run/node";
import { isRouteErrorResponse } from "@remix-run/react";
import type { MetaFunction } from "@remix-run/react";
import { getSession } from "~/utils";

export async function loader({ request }: LoaderFunctionArgs) {
  // Check if the user has a session token, and redirect them accordingly.
  const session = await getSession(request.headers.get("Cookie"));
  if (session.get("token")) {
    return redirect("/credentials");
  }
  return redirect("/login");
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
