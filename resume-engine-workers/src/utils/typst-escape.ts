/**
 * Escape special Typst characters in text content.
 * Typst special chars: #, $, *, _, @, ~, \, <, >
 * We escape them so they appear as literal characters in the output.
 */
export function typstEscape(text: string): string {
  if (!text) return "";
  return text
    .replace(/\\/g, "\\\\")
    .replace(/#/g, "\\#")
    .replace(/\$/g, "\\$")
    .replace(/\*/g, "\\*")
    .replace(/_/g, "\\_")
    .replace(/@/g, "\\@")
    .replace(/~/g, "\\~")
    .replace(/</g, "\\<")
    .replace(/>/g, "\\>");
}

/**
 * Recursively escape all string values in a data structure for Typst.
 */
export function typstEscapeDeep(data: unknown): unknown {
  if (typeof data === "string") {
    return typstEscape(data);
  }
  if (Array.isArray(data)) {
    return data.map(typstEscapeDeep);
  }
  if (data !== null && typeof data === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
      result[key] = typstEscapeDeep(value);
    }
    return result;
  }
  return data;
}
