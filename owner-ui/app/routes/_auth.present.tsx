import { FormControlLabel, Paper, Switch, Typography } from "@mui/material";
import { json, type ActionFunctionArgs } from "@remix-run/node";
import { Form, useActionData } from "@remix-run/react";
import { FlexContainer } from "~/components/FlexContainer";
import { AuthorizationRequestObject } from "~/interfaces/AuthorizationRequestObject";

export async function action({ request }: ActionFunctionArgs) {
  const body = await request.formData();
  let resp, data: AuthorizationRequestObject;
  switch (body.get("intent")) {
    case "choose-cred":
      resp = await fetch(
        `https://owner-lib:${process.env.CS3900_OWNER_AGENT_PORT}/presentation/init?${body.get("query")}`,
      );
      data = await resp.json();
      return json(data);
      break;

    default:
      break;
  }
}

export default function Present() {
  const data = useActionData<typeof action>();
  const definition = data?.presentation_definition;

  return (
    <FlexContainer component="main" maxWidth="xl">
      <Form>
        {definition?.input_descriptors.map((input_descriptor) => {
          return (
            <>
              <Paper key={definition.id}>
                <Typography>{input_descriptor.name}</Typography>
                {input_descriptor.constraints.fields[0].optional && (
                  <FormControlLabel
                    label={input_descriptor.name}
                    control={<Switch />}
                  />
                )}
              </Paper>
            </>
          );
        })}
      </Form>
    </FlexContainer>
  );
}
