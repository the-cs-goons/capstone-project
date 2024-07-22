import { PresentationDefinition } from "~/interfaces/PresentationDefinition/PresentationDefinition";

export interface AuthorizationRequestObject {
  client_id: string;
  client_id_scheme: string;
  client_metadata: object;
  presentation_definition: PresentationDefinition;
  response_uri: string;
  response_type: string;
  response_mode: string;
  nonce: string;
  wallet_nonce: string | null;
  state: string | null;
}
