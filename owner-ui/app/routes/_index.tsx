import { isRouteErrorResponse } from "@remix-run/react";
import type { MetaFunction } from "@remix-run/react";

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
