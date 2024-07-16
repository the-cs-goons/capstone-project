import { Card, CardActionArea, CardContent, CardHeader } from "@mui/material";
import { Link } from "@remix-run/react";

interface CredentialDataField {
  id: string;
  issuer_name: string | null;
  issuer_url: string;
  credential_configuration_id: string;
  credential_configuration_name: string | null;
  is_deferred: boolean;
  c_type: string;
  raw_sdjwtvc?: string;
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
      <CardActionArea
        component={Link}
        // TODO - change this
        to={credential.credential_configuration_id ?? "error"}
        sx={{ height: "100%" }}
      >
        <CardHeader
          title={credential.credential_configuration_id ?? "Pending credential"}
          titleTypographyProps={{ component: "h2", noWrap: true }}
          subheader={credential.issuer_name}
          subheaderTypographyProps={{ variant: "subtitle1" }}
        />
        <CardContent>
          {credential.raw_sdjwtvc ? "Real credential" : "Pending approval"}
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
