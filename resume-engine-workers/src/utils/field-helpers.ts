/**
 * Get a field value with fallback options and a default value.
 * Port of Python's get_field_with_fallback used by all templates.
 */
export function getFieldWithFallback<T = unknown>(
  obj: Record<string, unknown>,
  primaryField: string,
  fallbackFields: string[] = [],
  defaultValue: T | undefined = undefined,
): T {
  if (primaryField in obj && obj[primaryField]) {
    return obj[primaryField] as T;
  }
  for (const fallback of fallbackFields) {
    if (fallback in obj && obj[fallback]) {
      return obj[fallback] as T;
    }
  }
  return defaultValue as T;
}

/**
 * Navigate a nested data path like "personalInfo.name" and return the value.
 */
export function getNestedField(
  data: Record<string, unknown>,
  path: string,
  defaultValue: unknown = undefined,
): unknown {
  const keys = path.split(".");
  let current: unknown = data;
  for (const key of keys) {
    if (current === null || current === undefined || typeof current !== "object") {
      return defaultValue;
    }
    current = (current as Record<string, unknown>)[key];
  }
  return current ?? defaultValue;
}
