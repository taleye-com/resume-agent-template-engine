import { describe, it, expect } from "vitest";
import { typstEscape, typstEscapeDeep } from "../../src/utils/typst-escape.js";
import {
  getFieldWithFallback,
  getNestedField,
} from "../../src/utils/field-helpers.js";

// ---------------------------------------------------------------------------
// typstEscape
// ---------------------------------------------------------------------------

describe("typstEscape", () => {
  it("escapes hash characters", () => {
    expect(typstEscape("C# is great")).toContain("\\#");
  });

  it("escapes asterisks", () => {
    expect(typstEscape("5 * 3")).toContain("\\*");
  });

  it("escapes underscores", () => {
    expect(typstEscape("var_name")).toContain("\\_");
  });

  it("escapes angle brackets", () => {
    const result = typstEscape("<html>");
    expect(result).toContain("\\<");
    expect(result).toContain("\\>");
  });

  it("escapes dollar signs", () => {
    expect(typstEscape("$100")).toContain("\\$");
  });

  it("escapes at signs", () => {
    expect(typstEscape("user@domain")).toContain("\\@");
  });

  it("escapes tildes", () => {
    expect(typstEscape("~approx")).toContain("\\~");
  });

  it("escapes backslashes", () => {
    expect(typstEscape("a\\b")).toContain("\\\\");
  });

  it("returns empty string for empty input", () => {
    expect(typstEscape("")).toBe("");
  });

  it("returns empty string for null/undefined-like input", () => {
    // typstEscape checks `if (!text) return ""` so falsy values return ""
    expect(typstEscape(null as unknown as string)).toBe("");
    expect(typstEscape(undefined as unknown as string)).toBe("");
  });

  it("does not double-escape already-escaped text", () => {
    // If we escape \\# it should become \\\\\\# (each special char escapes)
    const result = typstEscape("\\#");
    expect(result).toBe("\\\\\\#");
  });

  it("handles strings with no special characters", () => {
    expect(typstEscape("Hello World")).toBe("Hello World");
  });
});

// ---------------------------------------------------------------------------
// typstEscapeDeep
// ---------------------------------------------------------------------------

describe("typstEscapeDeep", () => {
  it("escapes string values in nested objects", () => {
    const input = { name: "C# developer", tags: ["a*b", "c_d"] };
    const result = typstEscapeDeep(input) as Record<string, unknown>;
    expect(result.name).toBe("C\\# developer");
    expect((result.tags as string[])[0]).toBe("a\\*b");
    expect((result.tags as string[])[1]).toBe("c\\_d");
  });

  it("preserves non-string values", () => {
    const input = { count: 42, active: true, data: null };
    const result = typstEscapeDeep(input) as Record<string, unknown>;
    expect(result.count).toBe(42);
    expect(result.active).toBe(true);
    expect(result.data).toBe(null);
  });
});

// ---------------------------------------------------------------------------
// getFieldWithFallback
// ---------------------------------------------------------------------------

describe("getFieldWithFallback", () => {
  it("returns primary field value", () => {
    const obj = { name: "John", title: "Mr" };
    expect(getFieldWithFallback(obj, "name", ["title"], "default")).toBe(
      "John",
    );
  });

  it("falls back to alternative field", () => {
    const obj: Record<string, unknown> = { title: "Engineer" };
    expect(getFieldWithFallback(obj, "position", ["title"], "default")).toBe(
      "Engineer",
    );
  });

  it("returns default when no field found", () => {
    const obj: Record<string, unknown> = { foo: "bar" };
    expect(getFieldWithFallback(obj, "name", ["title"], "default")).toBe(
      "default",
    );
  });

  it("returns undefined when no field found and no default", () => {
    const obj: Record<string, unknown> = {};
    expect(getFieldWithFallback(obj, "name", [])).toBeUndefined();
  });

  it("skips falsy primary values and falls back", () => {
    // getFieldWithFallback checks truthiness, so empty string is falsy
    const obj: Record<string, unknown> = { name: "", nickname: "Johnny" };
    expect(getFieldWithFallback(obj, "name", ["nickname"], "default")).toBe(
      "Johnny",
    );
  });

  it("returns the first truthy fallback", () => {
    const obj: Record<string, unknown> = { b: "", c: "found" };
    expect(getFieldWithFallback(obj, "a", ["b", "c"], "default")).toBe("found");
  });
});

// ---------------------------------------------------------------------------
// getNestedField
// ---------------------------------------------------------------------------

describe("getNestedField", () => {
  it("navigates nested paths", () => {
    const obj = { a: { b: { c: "deep" } } };
    expect(getNestedField(obj, "a.b.c")).toBe("deep");
  });

  it("returns default for missing path", () => {
    const obj: Record<string, unknown> = { a: { b: 1 } };
    expect(getNestedField(obj, "a.c.d", "fallback")).toBe("fallback");
  });

  it("returns default for null intermediate", () => {
    const obj: Record<string, unknown> = { a: null };
    expect(getNestedField(obj, "a.b", "fallback")).toBe("fallback");
  });

  it("returns value at single-level path", () => {
    const obj: Record<string, unknown> = { foo: "bar" };
    expect(getNestedField(obj, "foo")).toBe("bar");
  });

  it("returns undefined as default when path missing and no default provided", () => {
    const obj: Record<string, unknown> = {};
    expect(getNestedField(obj, "x.y")).toBeUndefined();
  });
});
