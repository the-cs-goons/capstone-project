import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import {
  AppBar,
  Button,
  FormControlLabel,
  IconButton,
  Paper,
  Switch,
  Toolbar,
  Typography,
} from "@mui/material";
import { json, SerializeFrom, type ActionFunctionArgs } from "@remix-run/node";
import {
  Form,
  redirect,
  useActionData,
  useNavigate,
  useSubmit,
} from "@remix-run/react";
import { AxiosResponse } from "axios";
import type { FormEvent } from "react";
import { FlexContainer } from "~/components/FlexContainer";
import type { AuthorizationRequestObject } from "~/interfaces/AuthorizationRequestObject";
import type { FieldSelectionObject } from "~/interfaces/PresentationDefinition/FieldSelectionObject";
import {
  authHeaders,
  getSessionFromRequest,
  walletBackendClient,
} from "~/utils";
import * as React from 'react';
import Snackbar from '@mui/material/Snackbar';
// import IconButton from '@mui/material/IconButton';
// import CloseIcon from '@mui/icons-material/Close';
import Alert from '@mui/material/Alert';

export async function action({ request }: ActionFunctionArgs) {
  const body:
    | { intent: "choose-cred"; query: string }
    | { intent: "present-cred"; data: FieldSelectionObject } =
    await request.json();
  let resp: AxiosResponse;
  let data: AuthorizationRequestObject;
  switch (body.intent) {
    case "choose-cred":
      resp = await walletBackendClient.get(`/presentation/init?${body.query}`, {
        headers: authHeaders(await getSessionFromRequest(request)),
      });
      data = await resp.data;
      return json(data);

    case "present-cred":
      resp = await walletBackendClient.post(`/presentation`, body.data, {
        headers: authHeaders(await getSessionFromRequest(request)),
      });
      // TODO: implement proper redirect
      console.log(resp.data);
      return redirect("/presentation_successful");

    default:
      break;
  }
}

export interface SnackbarMessage {
  message: string;
  key: number;
}

export default function Present() {
  const data = useActionData<typeof action>();
  const definition = data?.presentation_definition;
  const submit = useSubmit();
  const navigate = useNavigate();

  const [snackPack, setSnackPack] = React.useState<readonly SnackbarMessage[]>([]);
  const [open, setOpen] = React.useState(false);
  const [messageInfo, setMessageInfo] = React.useState<SnackbarMessage | undefined>(
    undefined,
  );

  React.useEffect(() => {
    if (snackPack.length && !messageInfo) {
      // Set a new snack when we don't have an active one
      setMessageInfo({ ...snackPack[0] });
      setSnackPack((prev) => prev.slice(1));
      setOpen(true);
    } else if (snackPack.length && messageInfo && open) {
      // Close an active snack when a new one is added
      setOpen(false);
    }
  }, [snackPack, messageInfo, open]);

  const handleClick = (message: string) => () => {
    setSnackPack((prev) => [...prev, { message, key: new Date().getTime() }]);
  };

  const handleClose = (event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpen(false);
  };

  const handleExited = () => {
    setMessageInfo(undefined);
  };

  function handlePresent(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const data: SerializeFrom<FieldSelectionObject> = { field_requests: [] };
    definition?.input_descriptors.forEach((input_descriptor) => {
      const formControl = event.currentTarget.elements.namedItem(
        input_descriptor.id,
      ) as HTMLInputElement | null;
      const approved = formControl?.checked ?? false;
      data.field_requests.push({
        field: input_descriptor.constraints.fields?.at(0) ?? {
          path: [],
          id: null,
          name: null,
          filter: null,
          optional: null,
        },
        input_descriptor_id: input_descriptor.id,
        approved: approved,
      });
    });

    submit(
      { data: data, intent: "present-cred" },
      {
        method: "post",
        encType: "application/json",
      },
    );
  }

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ pb: 2, pt: 1, minHeight: 128, alignItems: "flex-end" }}>
          <IconButton
            color="inherit"
            aria-label="Back"
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
            Choose information
          </Typography>
        </Toolbar>
      </AppBar>
      <FlexContainer component="main" maxWidth="xl">
        <Form method="post" onSubmit={handlePresent}>
          <Typography>
            {data?.client_id} is requesting the following data.
          </Typography>
          {definition?.input_descriptors.map((input_descriptor) => {
            return (
              <Paper key={input_descriptor.id} sx={{ p: 3, mt: 10 }}>
                <FormControlLabel
                  label={input_descriptor.name ?? input_descriptor.id}
                  control={
                    input_descriptor.constraints.fields?.at(0)?.optional ? (
                      <Switch name={input_descriptor.id} />
                    ) : (
                      <input
                        type="hidden"
                        name={input_descriptor.id}
                        checked
                        readOnly
                      />
                    )
                  }
                />
              </Paper>
            );
          })}
          <Button type="submit">Present</Button>
          <Button type="button" color="error" onClick={() => navigate(-1)}>
            Reject
          </Button>
          <div>
          <Button onClick={handleClick("pending")}>Open Pending Snackbar</Button>
          <Button onClick={handleClick("success")}>Open Success Snackbar</Button>
          <Snackbar
            key={messageInfo ? messageInfo.key : undefined}
            open={open}
            autoHideDuration={6000}
            onClose={handleClose}
            TransitionProps={{ onExited: handleExited }}
            message={messageInfo ? messageInfo.message : undefined}
          >
            <Alert
              onClose={handleClose}
              severity="info"
              variant="filled"
              sx={{ width: '100%' }}
            >
              {messageInfo ? messageInfo.message : undefined}
            </Alert>
          </Snackbar>
        </div>
      </Form>
      </FlexContainer>
    </>
  );
}
