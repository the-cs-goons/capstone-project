export interface Filter {
  type: "string" | "number" | "integer" | "boolean" | "array" | "object" | null;
  format: "date" | "date-time" | "email" | "uri" | null;

  min_length: number | null;
  max_length: number | null;
  pattern: string | null;

  minimum: number | null;
  exclusiveMinimum: boolean | null;
  maximum: number | null;
  exclusiveMaximum: boolean | null;
}
