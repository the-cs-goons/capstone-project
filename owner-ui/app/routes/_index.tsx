import {
  Card,
  Container,
  Typography,
  Unstable_Grid2 as Grid,
} from "@mui/material";
import { isRouteErrorResponse, useLoaderData } from "@remix-run/react";
import { json } from "@remix-run/node";
import type { MetaFunction, LoaderFunction } from "@remix-run/node";

export const meta: MetaFunction = ({ error }) => {
  let title = "SSI Wallet";
  if (error) {
    title = isRouteErrorResponse(error)
      ? `${error.status} ${error.statusText}`
      : "Error!";
  }
  return [
    {
      title: title,
    },
    { name: "description", content: "Take control of your identity." },
  ];
};

export const loader: LoaderFunction = async () => {
  const resp = await fetch(
    `http://owner-lib:${process.env.CS3900_OWNER_AGENT_PORT}/credentials`,
    { method: "GET" },
  );
  // TODO: make this more concrete
  const data: {
    id: string;
    type: string;
    issuer_name: string | null;
    token: string | null;
  }[] = await resp.json();
  return json(data);
};

export default function Index() {
  const credentials: {
    id: string;
    type: string;
    issuer_name: string | null;
    token: string | null;
  }[] = useLoaderData();
  return (
    <Container component="main">
      <Grid
        container
        columns={{ xs: 4, sm: 8, md: 12 }}
        spacing={{ xs: 2, md: 3 }}
        marginTop={{ xs: 1, md: 1.5 }}
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
                      JSON.parse(atob(credential.token)) as [string, string][],
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
    </Container>
  );
}
