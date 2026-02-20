import type {
  ApiErrorEnvelopeV1,
  ApiFieldErrorV1,
  GeneratePathwayRequestV1,
  GeneratePathwayResponseV1,
  GePatternV1,
  MetadataItemV1,
  MetadataResponseV1,
  PlanCourseV1,
  PlanTermV1,
  WarningPayloadV1,
} from "@shared_types/v1";

export type GePattern = GePatternV1;
export type MetadataItem = MetadataItemV1;
export type MetadataResponse = MetadataResponseV1;
export type GeneratePathwayRequest = GeneratePathwayRequestV1;
export type PlanCourse = PlanCourseV1;
export type PlanTerm = PlanTermV1;
export type WarningItem = WarningPayloadV1;
export type GeneratePathwayResponse = GeneratePathwayResponseV1;

export type ApiFieldError = ApiFieldErrorV1;
export type ApiErrorEnvelope = Partial<ApiErrorEnvelopeV1> & {
  error?: Partial<ApiErrorEnvelopeV1["error"]> & {
    details?: ApiFieldError[];
  };
};

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
