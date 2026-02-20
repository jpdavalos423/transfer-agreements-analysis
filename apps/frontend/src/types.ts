export type GePattern = "IGETC" | "7CoursePattern";

export interface MetadataItem {
  id: string;
  name: string;
}

export interface MetadataResponse {
  version: string;
  data: MetadataItem[];
}

export interface GeneratePathwayRequest {
  college_id: string;
  target_ucs: string[];
  ge_pattern: GePattern;
  completed_courses: string[];
}

export interface PlanCourse {
  courseCode: string;
  units: number | string;
}

export interface PlanTerm {
  term: string;
  courses: PlanCourse[];
}

export interface WarningDetail {
  field: string;
  message: string;
}

export interface WarningItem {
  severity?: string;
  message?: string;
  details?: WarningDetail[];
  source?: string;
}

export interface GeneratePathwayResponse {
  version: string;
  request_id?: string;
  plan: PlanTerm[];
  warnings: WarningItem[];
  unmet_requirements?: unknown[];
  incomplete?: boolean;
  completion_status?: string;
  completion_flags?: {
    complete?: boolean;
    is_complete?: boolean;
  };
  meta?: {
    incomplete?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ApiFieldError {
  field: string;
  message: string;
}

export interface ApiErrorEnvelope {
  version?: string;
  request_id?: string;
  error?: {
    code?: string;
    message?: string;
    status?: number;
    path?: string;
    details?: ApiFieldError[];
  };
}

export class ApiRequestError extends Error {
  code: string;
  details: ApiFieldError[];
  status: number;
  path: string;

  constructor(init: {
    code: string;
    message: string;
    details?: ApiFieldError[];
    status?: number;
    path?: string;
  }) {
    super(init.message);
    this.name = "ApiRequestError";
    this.code = init.code;
    this.details = init.details ?? [];
    this.status = init.status ?? 0;
    this.path = init.path ?? "";
  }
}
