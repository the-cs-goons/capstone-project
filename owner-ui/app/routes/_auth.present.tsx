import { Button, FormControlLabel, Paper, Switch } from "@mui/material";
import { json, SerializeFrom, type ActionFunctionArgs } from "@remix-run/node";
import { Form, redirect, useActionData, useSubmit } from "@remix-run/react";
import { AxiosResponse } from "axios";
import type { FormEvent } from "react";
import { FlexContainer } from "~/components/FlexContainer";
import type { AuthorizationRequestObject } from "~/interfaces/AuthorizationRequestObject";
import type { FieldSelectionObject } from "~/interfaces/PresentationDefinition/FieldSelectionObject";
import {
  authHeaders,
  getSessionFromRequest,
  walletBackendClient,
} from "~/utils";

export async function action({ request }: ActionFunctionArgs) {
  const body:
    | { intent: "choose-cred"; query: string }
    | { intent: "present-cred"; data: FieldSelectionObject } =
    await request.json();
  let resp: AxiosResponse;
  let data: AuthorizationRequestObject;
  switch (body.intent) {
    case "choose-cred":
      resp = await walletBackendClient.get(
        `/presentation/init?${body.query}`,
        {
          headers: authHeaders(await getSessionFromRequest(request)),
        }
      );
      data = await resp.data;
      return json(data);

    case "present-cred":
      resp = await walletBackendClient.post(`/presentation`, {
        headers: authHeaders(await getSessionFromRequest(request)),
        body: body.data,
      });
      // TODO: implement proper redirect
      console.log(resp.data);
      return redirect("/credentials");

    default:
      break;
  }
}

export default function Present() {
  const data = useActionData<typeof action>();
  const definition = data?.presentation_definition;
  const submit = useSubmit();

  function handlePresent(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const data: SerializeFrom<FieldSelectionObject> = { field_requests: [] };
    definition?.input_descriptors.forEach((input_descriptor) => {
      const formControl = event.currentTarget.elements.namedItem(
        input_descriptor.id,
      ) as HTMLInputElement | null;
      const approved = formControl?.checked ?? false;
      data.field_requests.push({
        field: input_descriptor.constraints.fields?.at(0) ?? {
          path: [],
          id: null,
          name: null,
          filter: null,
          optional: null,
        },
        input_descriptor_id: input_descriptor.id,
        approved: approved,
      });
    });

    submit(
      { data: data, intent: "present-cred" },
      {
        method: "post",
        encType: "application/json",
      },
    );
  }

  return (
    <FlexContainer component="main" maxWidth="xl">
      <Form method="post" onSubmit={handlePresent}>
        {definition?.input_descriptors.map((input_descriptor) => {
          return (
            <Paper key={input_descriptor.id}>
              <FormControlLabel
                label={input_descriptor.name ?? input_descriptor.id}
                control={
                  input_descriptor.constraints.fields?.at(0)?.optional ? (
                    <Switch name={input_descriptor.id} />
                  ) : (
                    <input
                      type="hidden"
                      name={input_descriptor.id}
                      checked
                      readOnly
                    />
                  )
                }
              />
            </Paper>
          );
        })}
        <Button type="submit" name="intent" value="present-cred">
          Present
        </Button>
      </Form>
    </FlexContainer>
  );
}
