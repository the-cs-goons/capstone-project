export interface CredentialOffer {
  credential_issuer: string;
  credential_configuration_ids: Array<string>;
  grants: object | null;
}
