import type { Field } from "~/interfaces/PresentationDefinition/Field";

export interface Constraint {
  fields: Array<Field> | null;
  limit_disclosure: "required" | "preferred" | null;
}
