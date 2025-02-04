import { CredentialOffer } from "./CredentialOffer";

export interface CredentialSelection {
  credential_configuration_id: string;
  credential_offer?: CredentialOffer | null;
  issuer_uri?: string | null;
}
