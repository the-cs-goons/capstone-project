import {
  ArrowBack as ArrowBackIcon,
  ExpandMore as ExpandMoreIcon,
} from "@mui/icons-material";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  AppBar,
  IconButton,
  Paper,
  Toolbar,
  Typography,
} from "@mui/material";
import type { LoaderFunctionArgs } from "@remix-run/node";
import {
  isRouteErrorResponse,
  json,
  useLoaderData,
  useNavigate,
  type MetaFunction,
} from "@remix-run/react";
import { FlexContainer } from "~/components/FlexContainer";
import type { BaseCredential } from "~/interfaces/Credential/BaseCredential";
import { decodeSdJwt, getClaims } from "@sd-jwt/decode";
import { digest } from "@sd-jwt/crypto-nodejs";
import { ReactNode } from "react";
import { authHeaderFromRequest, walletBackendClient } from "~/utils";
import { AxiosResponse } from "axios";

// TODO: fix typing in this component

export async function loader({ params, request }: LoaderFunctionArgs) {
  const resp = await walletBackendClient.get(
    `/credentials/${params.cred_id}`,
    { headers: await authHeaderFromRequest(request) }
  );
  const r = resp as AxiosResponse
  const credential: BaseCredential = await r.data;
  let claims;
  if ("raw_sdjwtvc" in credential) {
    const decodedCredential = await decodeSdJwt(
      credential.raw_sdjwtvc as string,
      digest,
    );
    claims = await getClaims<{ iat: number }>(
      decodedCredential.jwt.payload,
      decodedCredential.disclosures,
      digest,
    );
  } else {
    claims = {};
  }
  return json({ credential, claims });
}

export const meta: MetaFunction<typeof loader> = ({ data, error }) => {
  let title = `${data?.credential.credential_configuration_name ?? data?.credential.credential_configuration_id ?? "Unknown credential"} - SSI Wallet`;
  if (error) {
    title = isRouteErrorResponse(error)
      ? `${error.status} ${error.statusText}`
      : "Error!";
  }
  return [
    {
      title: title,
    },
    {
      name: "description",
      content: `${data?.credential.credential_configuration_name ?? data?.credential.credential_configuration_id ?? "Unknown credential"}`,
    },
  ];
};

export default function SingleCredential() {
  const { credential, claims } = useLoaderData<typeof loader>();
  const navigate = useNavigate();

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <IconButton
            color="inherit"
            aria-label="Add new credential"
            onClick={() => navigate(-1)}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography
            variant="h4"
            component="h1"
            id="credentials-appbar-title"
            flexGrow={1}
          >
            {credential.credential_configuration_name ??
              credential.credential_configuration_id}
          </Typography>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl">
        <Typography variant="h6" component="span">
          Issued by {credential.issuer_name ?? credential.issuer_url}
        </Typography>
        {credential.is_deferred ? (
          <Typography variant="h5" component="span">
            Pending approval by issuer
          </Typography>
        ) : (
          <>
            <Typography variant="h5" component="h2">
              Attributes
            </Typography>
            <Paper>
              {Object.entries(claims).map(([key, value]) => {
                return (
                  <Accordion key={key}>
                    <AccordionSummary
                      id={`${key}-header`}
                      aria-controls={`${key}-content`}
                      expandIcon={<ExpandMoreIcon />}
                    >
                      <Typography>{key}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography>{value as ReactNode}</Typography>
                    </AccordionDetails>
                  </Accordion>
                );
              })}
            </Paper>
          </>
        )}
      </FlexContainer>
    </>
  );
}
