function isDetail(value) {
  return (
    value &&
    typeof value === "object" &&
    typeof value.field === "string" &&
    typeof value.message === "string"
  );
}

export function mapApiErrorToUiStateRuntime(error) {
  if (error && typeof error === "object") {
    const maybe = error;
    if (typeof maybe.code === "string" && typeof maybe.message === "string") {
      const details = Array.isArray(maybe.details)
        ? maybe.details.filter(isDetail).map((d) => ({ field: d.field, message: d.message }))
        : [];
      return {
        code: maybe.code,
        message: maybe.message,
        details,
      };
    }
  }

  return {
    code: "REQUEST_FAILED",
    message: "Unable to complete request. Please try again.",
    details: [],
  };
}
