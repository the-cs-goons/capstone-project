import { Box, Container } from "@mui/material";
import { Scanner } from "@yudiel/react-qr-scanner";

export default function Scan() {
  return (
    <Container component="main">
      <Box sx={{ margin: "auto", textAlign: "center", width: 400 }}>
        <Scanner
          styles={{ container: { marginTop: 5 } }}
          onScan={(result) => console.log(result)}
        />
      </Box>
    </Container>
  );
}
