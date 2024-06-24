import { Card, Container, Unstable_Grid2 as Grid } from "@mui/material";

export const meta = () => {
  return [
    { title: "SSI Wallet" },
    { name: "description", content: "Take control of your identity." },
  ];
};

export default function Index() {
  return (
    <Container component="main">
      <Grid container>
        <Grid>
          <Card>hey!</Card>
        </Grid>
        <Grid>
          <Card>hi!</Card>
        </Grid>
        <Grid>
          <Card>hello!</Card>
        </Grid>
      </Grid>
    </Container>
  );
}
