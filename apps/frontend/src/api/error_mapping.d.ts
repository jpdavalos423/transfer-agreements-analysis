export interface UiApiErrorStateRuntime {
  code: string;
  message: string;
  details: Array<{ field: string; message: string }>;
}

export function mapApiErrorToUiStateRuntime(error: unknown): UiApiErrorStateRuntime;
