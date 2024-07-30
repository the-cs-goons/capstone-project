import { LoaderFunctionArgs } from "@remix-run/node";
import { redirect } from "@remix-run/react";
import { destroySession, getSessionFromRequest, walletBackendClient } from "~/utils";

export async function loader({ request }: LoaderFunctionArgs) {
    const session = await getSessionFromRequest(request);
    await walletBackendClient.get("/logout");
    return redirect("/login", {
        headers: {
        "Set-Cookie": await destroySession(session),
        },
    });
}