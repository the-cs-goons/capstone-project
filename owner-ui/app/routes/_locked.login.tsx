import { Button, Stack, TextField, Typography } from "@mui/material";
import { ActionFunctionArgs } from "@remix-run/node";
import {
  Form,
  json,
  redirect,
  useActionData,
  useLoaderData,
} from "@remix-run/react";
import { useState } from "react";
import { commitSession, getSession, walletBackendClient } from "~/utils";
import { AxiosError, isAxiosError } from "axios";

interface Login {
  access_token: string;
  username: string;
}

export async function action({ request }: ActionFunctionArgs) {
  const body = await request.formData();

  try {
    const resp = await walletBackendClient.post(
      "/login",
      Object.fromEntries(body),
    );
    const user = (await resp.data) as Login;
    const session = await getSession(request.headers.get("Cookie"));
    session.set("token", user.access_token);
    return json(
      { username: user.username },
      {
        headers: {
          "Set-Cookie": await commitSession(session),
        },
      },
    );
  } catch (error) {
    if (isAxiosError(error)) {
      const e = error as AxiosError;
      const data = e.response?.data as { detail: string };
      return data.detail;
    }
    return `Error: ${error}`;
  }
}

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const errors = useActionData<typeof action>();
  const login_user = useLoaderData();
  if (login_user) {
    return redirect("/credentials");
  }
  return (
    <Stack spacing={2}>
      <Form method="POST" action="/login">
        <TextField
          label="Username"
          id="login-username"
          type="text"
          name="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          variant="filled"
          required
        />
        <TextField
          label="Password"
          id="login-password"
          type="password"
          name="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          variant="filled"
          required
        />
        <Button type="submit" variant="contained">
          Login
        </Button>
        {errors && <Typography>{`${errors}`}</Typography>}
      </Form>
    </Stack>
  );
}
