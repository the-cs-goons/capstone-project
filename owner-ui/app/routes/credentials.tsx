import { Card, Typography, Unstable_Grid2 as Grid } from "@mui/material";
import type { LoaderFunction } from "@remix-run/node";
import {
  isRouteErrorResponse,
  json,
  useLoaderData,
  type MetaFunction,
} from "@remix-run/react";
import { CredentialsGridContainer } from "~/components/CredentialsGridContainer";
import { FlexContainer } from "~/components/FlexContainer";

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

interface CredentialDataField {
  id: string;
  type: string;
  issuer_name: string | null;
  token: string | null;
}

export const loader: LoaderFunction = async () => {
  const resp = await fetch(
    `http://owner-lib:${process.env.CS3900_OWNER_AGENT_PORT}/credentials`,
    { method: "GET" },
  );
  const data: Array<CredentialDataField> = await resp.json();
  return json(data);
};

export default function Credentials() {
  const credentials: Array<CredentialDataField> = useLoaderData();

  return (
    <FlexContainer component="main" maxWidth="xl" disableGutters={true}>
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
                <Card>
                  <Typography variant="h4">{credential.type}</Typography>
                  <Typography variant="h6">{credential.issuer_name}</Typography>
                  {credential.token
                    ? Object.entries(
                        JSON.parse(atob(credential.token)) as [
                          string,
                          string,
                        ][],
                      ).map(([key, value]) => {
                        return (
                          <Typography variant="body1" key={key}>
                            {value}
                          </Typography>
                        );
                      })
                    : "Pending approval"}
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </CredentialsGridContainer>
    </FlexContainer>
  );
}
