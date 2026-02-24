import { describe, it, expect } from "vitest";
import {
  DocumentRequestSchema,
  ValidationRequestSchema,
  AnalyzeRequestSchema,
} from "../../src/schemas/requests.js";

// ---------------------------------------------------------------------------
// DocumentRequestSchema
// ---------------------------------------------------------------------------

describe("DocumentRequestSchema", () => {
  it("validates a minimal generate request", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "resume",
      template: "classic",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
      format: "pdf",
    });
    expect(result.success).toBe(true);
  });

  it("defaults spacing_mode to compact", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "resume",
      template: "classic",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
      format: "pdf",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.spacing_mode).toBe("compact");
    }
  });

  it("defaults format to pdf when omitted", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "resume",
      template: "classic",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.format).toBe("pdf");
    }
  });

  it("rejects invalid document_type", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "invalid",
      template: "classic",
      data: {},
      format: "pdf",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing template", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "resume",
      template: "",
      data: {},
      format: "pdf",
    });
    expect(result.success).toBe(false);
  });

  it("accepts cover_letter document type", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "cover_letter",
      template: "classic",
      data: { personalInfo: { name: "T", email: "t@t.com" }, body: "text" },
      format: "typst",
    });
    expect(result.success).toBe(true);
  });

  it("defaults ultra_validation to false", () => {
    const result = DocumentRequestSchema.safeParse({
      document_type: "resume",
      template: "classic",
      data: {},
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.ultra_validation).toBe(false);
    }
  });
});

// ---------------------------------------------------------------------------
// ValidationRequestSchema
// ---------------------------------------------------------------------------

describe("ValidationRequestSchema", () => {
  it("validates a standard validation request", () => {
    const result = ValidationRequestSchema.safeParse({
      document_type: "resume",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
    });
    expect(result.success).toBe(true);
  });

  it("defaults validation_level to standard", () => {
    const result = ValidationRequestSchema.safeParse({
      document_type: "resume",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.validation_level).toBe("standard");
    }
  });

  it("accepts custom validation level string", () => {
    const result = ValidationRequestSchema.safeParse({
      document_type: "resume",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
      validation_level: "ultra",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.validation_level).toBe("ultra");
    }
  });

  it("rejects invalid document_type", () => {
    const result = ValidationRequestSchema.safeParse({
      document_type: "essay",
      data: {},
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AnalyzeRequestSchema
// ---------------------------------------------------------------------------

describe("AnalyzeRequestSchema", () => {
  it("validates a basic analyze request", () => {
    const result = AnalyzeRequestSchema.safeParse({
      document_type: "resume",
      template: "classic",
      data: { personalInfo: { name: "Test", email: "t@t.com" } },
    });
    expect(result.success).toBe(true);
  });

  it("defaults spacing_mode to compact", () => {
    const result = AnalyzeRequestSchema.safeParse({
      document_type: "resume",
      template: "two-column",
      data: {},
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.spacing_mode).toBe("compact");
    }
  });

  it("rejects missing template", () => {
    const result = AnalyzeRequestSchema.safeParse({
      document_type: "resume",
      template: "",
      data: {},
    });
    expect(result.success).toBe(false);
  });
});
