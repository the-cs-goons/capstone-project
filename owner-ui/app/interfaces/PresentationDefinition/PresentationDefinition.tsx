import type { InputDescriptor } from "~/interfaces/PresentationDefinition/InputDescriptor";

export interface PresentationDefinition {
  id: string;
  input_descriptors: Array<InputDescriptor>;
  name: string | null;
  purpose: string | null;
}
