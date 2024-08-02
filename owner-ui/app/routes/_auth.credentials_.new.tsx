import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import {
  AppBar,
  Box,
  Button,
  FormControlLabel,
  IconButton,
  Paper,
  Switch,
  Toolbar,
  Typography,
} from "@mui/material";
import { ActionFunctionArgs, redirect, SerializeFrom } from "@remix-run/node";
import {
  Form,
  isRouteErrorResponse,
  useActionData,
  useNavigate,
  useSubmit,
  type MetaFunction,
} from "@remix-run/react";
import { Scanner } from "@yudiel/react-qr-scanner";
import { AxiosResponse, isAxiosError } from "axios";
import { FormEvent } from "react";
import { FlexContainer } from "~/components/FlexContainer";
import { CredentialOffer } from "~/interfaces/Credential/CredentialOffer";
import { CredentialSelection } from "~/interfaces/Credential/CredentialSelection";
import {
  authHeaders,
  getSessionFromRequest,
  walletBackendClient,
} from "~/utils";

export const meta: MetaFunction = ({ error }) => {
  let title = "Credentials - SSI Wallet";
  if (error) {
    title = isRouteErrorResponse(error)
      ? `${error.status} ${error.statusText}`
      : "Error!";
  }
  return [
    {
      title: title,
    },
    { name: "description", content: "View and manage credentials" },
  ];
};

export async function action({ request }: ActionFunctionArgs) {
  const body:
    | { intent: "get-offer"; query: string }
    | {
        intent: "submit-request";
        configs: Array<string>;
        offer: CredentialOffer;
      } = await request.json();
  let resp: AxiosResponse;
  let data: CredentialOffer;
  let selection: CredentialSelection;
  switch (body.intent) {
    case "get-offer":
      resp = await walletBackendClient.get(`/offer?${body.query}`, {
        headers: authHeaders(await getSessionFromRequest(request)),
      });
      data = resp.data;
      return data;

    case "submit-request":
      // TODO: fix this hack
      selection = {
        credential_configuration_id: body.configs.at(0) ?? "InvalidId",
        credential_offer: body.offer,
      };

      try {
        await walletBackendClient.post("/offer", selection, {
          headers: authHeaders(await getSessionFromRequest(request)),
          maxRedirects: 0,
        });
      } catch (error) {
        if (isAxiosError(error)) {
          if (error.response) {
            return redirect(error.response.headers["location"]);
          }
        }
      }
      break;

    default:
      break;
  }
}

export default function NewCredentialForm() {
  const navigate = useNavigate();
  const submit = useSubmit();
  const actionData = useActionData<typeof action>();

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const data: SerializeFrom<Array<string>> = [];
    actionData?.credential_configuration_ids.forEach((config) => {
      const formControl = event.currentTarget.elements.namedItem(
        config,
      ) as HTMLInputElement | null;
      const requested = formControl?.checked ?? false;
      if (requested) {
        data.push(config);
      }
    });

    submit(
      {
        configs: data,
        offer: actionData,
        intent: "submit-request",
      },
      { method: "post", encType: "application/json" },
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
            Add new credential
          </Typography>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl">
        {actionData ? (
          <Form method="post" onSubmit={handleSubmit}>
            <Typography>Select a credential type(s) to request.</Typography>
            {actionData.credential_configuration_ids.map((config) => {
              return (
                <Paper key={config} sx={{ p: 3, mt: 10 }}>
                  <FormControlLabel
                    label={config}
                    control={<Switch name={config} />}
                  />
                </Paper>
              );
            })}
            <Button type="submit">Send request</Button>
          </Form>
        ) : (
          <>
            <Typography>Scan the issuer&apos;s QR code</Typography>
            <Box
              sx={{
                width: "fit-content",
                height: "fit-content",
              }}
            >
              <Scanner
                styles={{
                  finderBorder: 50,
                }}
                onScan={(result) =>
                  submit(
                    { query: result[0].rawValue, intent: "get-offer" },
                    {
                      method: "post",
                      encType: "application/json",
                    },
                  )
                }
              />
            </Box>
          </>
        )}
      </FlexContainer>
    </>
  );
}
