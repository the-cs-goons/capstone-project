import { Filter } from "~/interfaces/PresentationDefinition/Filter";

export interface Field {
  path: Array<string>;
  id: string | null;
  name: string | null;
  filter: Filter | null;
  optional: boolean | null;
}
