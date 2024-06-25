import { Card, Container, Typography, Unstable_Grid2 as Grid } from "@mui/material";
import { useLoaderData } from "@remix-run/react";
import { json } from "@remix-run/node";

export const meta = () => {
  return [
    { title: "SSI Wallet" },
    { name: "description", content: "Take control of your identity." },
  ];
};

export const loader = async () => {
  const resp = await fetch(`http://localhost:8081/credentials`, { method: "GET" });
  const data = await resp.json();
  return json(data);
};

export default function Index() {
  const credentials = useLoaderData();
  return (
    <Container component="main">
      <Grid
        container
        columns={{ xs: 4, sm: 8, md: 12 }}
        spacing={{ xs: 2, md: 3 }}
        marginTop={{ xs: 1, md: 1.5 }}
      >
        {credentials?.map((credential) => {
            return (
              <Grid
                xs={4}
                key={credential.id}
                sx={{ display: 'flex' }}
                justifyContent={'center'}
              >
                <Card>
                  <Typography variant="h4">{credential.type}</Typography>
                  
                  {credential.token
                    ? Object.entries(JSON.parse(atob(credential.token))).map(([key, value]) => {
                      return <Typography variant="body1" key={key}>{value}</Typography>;
                    })
                    : "Pending approval"
                  }
                </Card>
              </Grid>
            )
          })
        }
      </Grid>
    </Container>
  );
}
