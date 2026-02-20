export const API_VERSION = "v1" as const;

export type GePatternV1 = "IGETC" | "7CoursePattern";
export type WarningSeverityV1 = "INFO" | "WARN" | "ERROR";

export interface ApiFieldErrorV1 {
  field: string;
  message: string;
}

export interface ApiErrorBodyV1 {
  code: string;
  message: string;
  status: number;
  path: string;
  details: ApiFieldErrorV1[];
}

export interface ApiErrorEnvelopeV1 {
  version: typeof API_VERSION;
  request_id: string;
  error: ApiErrorBodyV1;
}

export interface MetadataItemV1 {
  id: string;
  name: string;
}

export interface MetadataResponseV1 {
  version: typeof API_VERSION;
  data: MetadataItemV1[];
}

export interface HealthRuntimeV1 {
  dataset_version: string;
  generated_at: string;
  row_counts: Record<string, number>;
}

export interface HealthResponseV1 {
  version: typeof API_VERSION;
  status: "ok" | "degraded";
  runtime: HealthRuntimeV1;
}

export interface GeneratePathwayRequestV1 {
  college_id: string;
  target_ucs: string[];
  ge_pattern: GePatternV1;
  completed_courses: string[];
}

export interface PlanCourseV1 {
  courseCode: string;
  units: number | string;
}

export interface PlanTermV1 {
  term: string;
  courses: PlanCourseV1[];
}

export interface WarningPayloadV1 {
  code: string;
  message: string;
  severity: WarningSeverityV1;
  source: string;
  trace_id: string;
  details: ApiFieldErrorV1[];
}

export interface GeneratePathwayResponseMetaV1 {
  college_id: string;
  target_ucs: string[];
  ge_pattern: GePatternV1;
  completed_courses_count: number;
  [key: string]: unknown;
}

export interface GeneratePathwayResponseV1 {
  version: typeof API_VERSION;
  request_id: string;
  plan: PlanTermV1[];
  warnings: WarningPayloadV1[];
  meta: GeneratePathwayResponseMetaV1;
  incomplete?: boolean;
  completion_status?: string;
  completion_flags?: {
    complete?: boolean;
    is_complete?: boolean;
  };
  unmet_requirements?: unknown[];
  [key: string]: unknown;
}
