export interface BaseCredential {
  id: string;
  issuer_name: string | null;
  issuer_url: string;
  credential_configuration_id: string;
  credential_configuration_name: string | null;
  is_deferred: boolean;
  c_type: string;
}
