import { Box, Container, Typography } from "@mui/material";
import { Outlet } from "@remix-run/react";

export default function Locked() {
  return (
    <Container component="main" sx={{ height: "100%" }}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          height: "100%",
          marginTop: "60px",
        }}
      >
        <Typography variant="h1">VC Wallet App</Typography>
        <Outlet />
      </Box>
    </Container>
  );
}
