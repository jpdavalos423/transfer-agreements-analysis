import {
  ApiErrorEnvelope,
  ApiRequestError,
  GeneratePathwayRequest,
  GeneratePathwayResponse,
  MetadataResponse,
} from "../types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function normalizeBaseUrl(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export function getApiBaseUrl(): string {
  const fromConfig = globalThis?.window?.__TPP_CONFIG__?.apiBaseUrl;
  if (typeof fromConfig === "string" && fromConfig.trim() !== "") {
    return normalizeBaseUrl(fromConfig.trim());
  }

  const fromInjectedGlobal = globalThis?.window?.__TPP_API_BASE_URL;
  if (typeof fromInjectedGlobal === "string" && fromInjectedGlobal.trim() !== "") {
    return normalizeBaseUrl(fromInjectedGlobal.trim());
  }

  const fromViteEnv = import.meta.env.VITE_API_BASE_URL;
  if (typeof fromViteEnv === "string" && fromViteEnv.trim() !== "") {
    return normalizeBaseUrl(fromViteEnv.trim());
  }

  return DEFAULT_API_BASE_URL;
}

function toApiRequestError(payload: unknown, fallback: { status: number; path: string }): ApiRequestError {
  const envelope = payload as ApiErrorEnvelope;
  const rawDetails = envelope?.error?.details;
  const details = Array.isArray(rawDetails)
    ? rawDetails
        .filter(
          (item): item is { field: string; message: string } =>
            Boolean(
              item &&
                typeof item === "object" &&
                typeof item.field === "string" &&
                typeof item.message === "string",
            ),
        )
        .map((item) => ({ field: item.field, message: item.message }))
    : [];

  return new ApiRequestError({
    code: envelope?.error?.code || "REQUEST_FAILED",
    message: envelope?.error?.message || "Unable to complete request. Please try again.",
    details,
    status:
      typeof envelope?.error?.status === "number"
        ? envelope.error.status
        : fallback.status,
    path: envelope?.error?.path || fallback.path,
  });
}

async function requestJson<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, options);
  let payload: unknown = null;

  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw toApiRequestError(payload, { status: response.status, path });
  }

  return payload as T;
}

export async function fetchColleges(): Promise<MetadataResponse> {
  return requestJson<MetadataResponse>("/v1/metadata/colleges", { method: "GET" });
}

export async function fetchUcs(): Promise<MetadataResponse> {
  return requestJson<MetadataResponse>("/v1/metadata/ucs", { method: "GET" });
}

export async function submitGeneratePathway(
  payload: GeneratePathwayRequest,
): Promise<GeneratePathwayResponse> {
  return requestJson<GeneratePathwayResponse>("/v1/pathways/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
