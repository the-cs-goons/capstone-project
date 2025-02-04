import { AccessToken } from "~/interfaces/AccessToken";
import { BaseCredential } from "~/interfaces/Credential/BaseCredential";

export interface DeferredCredential extends BaseCredential {
  transaction_id: string;
  deferred_credential_endpoint: string;
  last_request: string;
  access_token: AccessToken;
}
