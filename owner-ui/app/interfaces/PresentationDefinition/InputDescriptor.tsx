import type { Constraint } from "~/interfaces/PresentationDefinition/Constraint";

export interface InputDescriptor {
  id: string;
  constraints: Constraint;
  name: string | null;
  purpose: string | null;
  format: string | null;
}
