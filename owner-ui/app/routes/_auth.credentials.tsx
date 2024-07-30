import { Add as AddIcon } from "@mui/icons-material";
import {
  Typography,
  Unstable_Grid2 as Grid,
  AppBar,
  Toolbar,
  Tooltip,
  IconButton,
} from "@mui/material";
import { ActionFunctionArgs, LoaderFunctionArgs } from "@remix-run/node";
import {
  isRouteErrorResponse,
  json,
  useLoaderData,
  type MetaFunction,
} from "@remix-run/react";
import { AxiosResponse } from "axios";
import { CredentialCard } from "~/components/CredentialCard";
import { CredentialsGridContainer } from "~/components/CredentialsGridContainer";
import { FlexContainer } from "~/components/FlexContainer";
import type { BaseCredential } from "~/interfaces/Credential/BaseCredential";
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

export async function loader({ request }: LoaderFunctionArgs) {
  const resp: AxiosResponse = await walletBackendClient.get(`/credentials`, {
    headers: authHeaders(await getSessionFromRequest(request)),
  });
  const data: Array<BaseCredential> = await resp.data;
  return json(data);
}

export async function action({ request }: ActionFunctionArgs) {
  const body = await request.formData();
  await walletBackendClient.delete(`/credentials/${body.get("id")}`, {
    headers: authHeaders(await getSessionFromRequest(request)),
  });
  return null;
}

export default function Credentials() {
  const credentials = useLoaderData<typeof loader>();

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <Typography
            variant="h4"
            component="h1"
            id="credentials-appbar-title"
            flexGrow={1}
          >
            Credentials
          </Typography>
          <Tooltip id="add-credential-tooltip" title="Add new credential">
            <IconButton color="inherit" aria-label="Add new credential">
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl" disableGutters>
        <CredentialsGridContainer>
          <Grid
            container
            columns={{ xs: 4, sm: 8, md: 12 }}
            spacing={{ xs: 2, sm: 3 }}
            sx={{ mt: { xs: 1, md: 1.5 } }}
          >
            {credentials.map((credential) => {
              return (
                <Grid
                  key={credential.id}
                  sx={{ display: "flex" }}
                  justifyContent={"center"}
                  size={4}
                >
                  <CredentialCard credential={credential} />
                </Grid>
              );
            })}
          </Grid>
        </CredentialsGridContainer>
      </FlexContainer>
    </>
  );
}
