import {
  Card,
  CardActionArea,
  CardContent,
  CardHeader,
  Divider,
} from "@mui/material";
import { Link } from "@remix-run/react";
import { BaseCredential } from "~/interfaces/Credential/BaseCredential";

export function CredentialCard({
  credential,
}: Readonly<{
  credential: BaseCredential;
}>) {
  return (
    <Card
      component="article"
      sx={{ minWidth: 100, width: "100%", aspectRatio: 16 / 9 }}
    >
      <CardActionArea
        component={Link}
        to={credential.id}
        sx={{ height: "100%" }}
      >
        <CardHeader
          title={
            credential.credential_configuration_name ??
            credential.credential_configuration_id
          }
          titleTypographyProps={{ component: "h2", noWrap: true }}
          subheader={credential.issuer_name ?? credential.issuer_url}
          subheaderTypographyProps={{ variant: "subtitle1" }}
        />
        <Divider />
        <CardContent>
          {"raw_sdjwtvc" in credential ? "Real credential" : "Pending approval"}
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
