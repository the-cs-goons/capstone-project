import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import {
  AppBar,
  Box,
  Button,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Toolbar,
  Typography,
} from "@mui/material";
import { ActionFunctionArgs } from "@remix-run/node";
import {
  Form,
  isRouteErrorResponse,
  useActionData,
  useNavigate,
  useSubmit,
  type MetaFunction,
} from "@remix-run/react";
import { Scanner } from "@yudiel/react-qr-scanner";
import { AxiosResponse } from "axios";
import { useState } from "react";
import { FlexContainer } from "~/components/FlexContainer";
import { CredentialOffer } from "~/interfaces/Credential/CredentialOffer";
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
    | { intent: "submit-request" } = await request.json();
  let resp: AxiosResponse;
  let data: CredentialOffer;
  switch (body.intent) {
    case "get-offer":
      resp = await walletBackendClient.get(`/offer?${body.query}`, {
        headers: authHeaders(await getSessionFromRequest(request)),
      });
      data = resp.data;
      return data;

    case "submit-request":
      return null;

    default:
      break;
  }
}

export default function NewCredentialForm() {
  const navigate = useNavigate();
  const submit = useSubmit();
  const data = useActionData<typeof action>();
  const [config, setConfig] = useState("");

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
        {data ? (
          <Form method="post">
            <Typography>Select a credential type</Typography>
            <FormControl fullWidth>
              <InputLabel id="credential-config-select-label">
                Credential type
              </InputLabel>
              <Select
                labelId="credential-config-select-label"
                id="credential-config-select"
                value={config}
                label="Credential type"
                onChange={(e: SelectChangeEvent) => {
                  setConfig(e.target.value);
                }}
              >
                {data.credential_configuration_ids.map((config) => {
                  return (
                    <MenuItem key={config} value={config}>
                      {config}
                    </MenuItem>
                  );
                })}
              </Select>
            </FormControl>
            <Button type="submit" name="intent" value="submit-request">
              Send request
            </Button>
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
