import {
  Card,
  CardActionArea,
  CardContent,
  CardHeader,
  Typography,
} from "@mui/material";
import { Link } from "@remix-run/react";

interface CredentialDataField {
  id: string;
  type: string;
  issuer_name: string | null;
  token: string | null;
}

export function CredentialCard({
  credential,
}: Readonly<{
  credential: CredentialDataField;
}>) {
  return (
    <Card
      component="article"
      sx={{ minWidth: 100, width: "100%", aspectRatio: 16 / 9 }}
    >
      <CardActionArea component={Link} to="test" sx={{ height: "100%" }}>
        <CardHeader
          title={credential.type}
          titleTypographyProps={{ component: "h2", noWrap: true }}
          subheader={credential.issuer_name}
          subheaderTypographyProps={{ variant: "subtitle1" }}
        />
        <CardContent>
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
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
