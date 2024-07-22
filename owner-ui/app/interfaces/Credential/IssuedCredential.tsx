import { BaseCredential } from "~/interfaces/Credential/BaseCredential";

export interface IssuedCredential extends BaseCredential {
  raw_sdjwtvc: string;
  received_at: string;
}
