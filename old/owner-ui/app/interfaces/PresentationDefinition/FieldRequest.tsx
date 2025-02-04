import { Field } from "~/interfaces/PresentationDefinition/Field";

export interface FieldRequest {
  field: Field;
  input_descriptor_id: string;
  approved: boolean;
}
