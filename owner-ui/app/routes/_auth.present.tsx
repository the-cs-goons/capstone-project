import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import {
  AppBar,
  Button,
  FormControlLabel,
  IconButton,
  Paper,
  Switch,
  Toolbar,
  Typography,
} from "@mui/material";
import { json, SerializeFrom, type ActionFunctionArgs } from "@remix-run/node";
import {
  Form,
  redirect,
  useActionData,
  useNavigate,
  useSubmit,
} from "@remix-run/react";
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
      resp = await walletBackendClient.get(`/presentation/init?${body.query}`, {
        headers: authHeaders(await getSessionFromRequest(request)),
      });
      data = await resp.data;
      return json(data);

    case "present-cred":
      try {
        resp = await walletBackendClient.post(`/presentation`, body.data, {
          headers: authHeaders(await getSessionFromRequest(request)),
        });
        if (resp.data.status == "OK") {
          return redirect("/presentation_successful");
        } else {
          const errorDetail = resp.data.errorDetail || "Unknown error";
          return redirect(
            `/presentation_fail?error=${encodeURIComponent(errorDetail)}`,
          );
        }
      } catch (error) {
        return redirect(`/presentation_fail?error=${error}`);
      }

    default:
      break;
  }
}

export default function Present() {
  const data = useActionData<typeof action>();
  const definition = data?.presentation_definition;
  const submit = useSubmit();
  const navigate = useNavigate();

  function handlePresent(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const data: SerializeFrom<FieldSelectionObject> = { field_requests: [] };
    definition?.input_descriptors.forEach((input_descriptor) => {
      input_descriptor.constraints.fields?.map((field) => {
        const formControl = event.currentTarget.elements.namedItem(
          field.id ?? field.path[0],
        ) as HTMLInputElement | null;
        const approved = formControl?.checked ?? false;
        data.field_requests.push({
          field: field ?? {
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
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <IconButton
            color="inherit"
            aria-label="Back"
            onClick={() => navigate(-1)}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography
            variant="h4"
            component="h1"
            id="credentials-appbar-title"
            flexGrow={1}
          >
            Choose information
          </Typography>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl">
        <Form method="post" onSubmit={handlePresent}>
          <Typography variant="h4" component="h2">
            {data?.client_id} is requesting the following data. Do you wish to
            proceed?
          </Typography>
          {definition?.input_descriptors.map((input_descriptor) => {
            return (
              <Paper key={input_descriptor.id} sx={{ p: 2 }}>
                <Typography variant="h5" component="h3">
                  {input_descriptor.name ?? input_descriptor.id}
                </Typography>
                <Typography>
                  {input_descriptor.purpose ?? "No purpose provided"}
                </Typography>
                {input_descriptor.constraints.fields?.map((field) => {
                  return (
                    <Paper key={field.id} sx={{ p: 2 }}>
                      <FormControlLabel
                        label={field.name ?? field.id}
                        control={
                          field.optional ? (
                            <Switch name={field.id ?? field.path[0]} />
                          ) : (
                            <input
                              type="hidden"
                              name={field.id ?? field.path[0]}
                              checked
                              readOnly
                            />
                          )
                        }
                      />
                    </Paper>
                  );
                })}
              </Paper>
            );
          })}
          <Button type="submit">Present</Button>
          <Button type="button" color="error" onClick={() => navigate(-1)}>
            Reject
          </Button>
        </Form>
      </FlexContainer>
    </>
  );
}
