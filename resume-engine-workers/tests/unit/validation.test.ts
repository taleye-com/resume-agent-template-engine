import { describe, it, expect } from "vitest";
import {
  validateResumeData,
  ultraValidateAndNormalize,
  enhancedValidate,
  validateDateFormat,
  ValidationLevel,
} from "../../src/validation/validator.js";

// ---------------------------------------------------------------------------
// validateDateFormat
// ---------------------------------------------------------------------------

describe("validateDateFormat", () => {
  it("accepts YYYY-MM format", () => {
    expect(validateDateFormat("2020-01")).toBe(true);
  });

  it("accepts YYYY-MM-DD format", () => {
    expect(validateDateFormat("2020-01-15")).toBe(true);
  });

  it("accepts 'Present' (case-insensitive)", () => {
    expect(validateDateFormat("Present")).toBe(true);
    expect(validateDateFormat("present")).toBe(true);
  });

  it("accepts empty string", () => {
    expect(validateDateFormat("")).toBe(true);
  });

  it("rejects free-form date strings", () => {
    expect(validateDateFormat("January 2020")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// validateResumeData
// ---------------------------------------------------------------------------

describe("validateResumeData", () => {
  it("passes valid data", () => {
    expect(() =>
      validateResumeData({
        personalInfo: { name: "Test", email: "test@example.com" },
      }),
    ).not.toThrow();
  });

  it("throws on missing personalInfo", () => {
    expect(() => validateResumeData({})).toThrow();
  });

  it("throws on missing name in personalInfo", () => {
    expect(() =>
      validateResumeData({
        personalInfo: { email: "test@example.com" },
      }),
    ).toThrow();
  });

  it("throws on missing email in personalInfo", () => {
    expect(() =>
      validateResumeData({
        personalInfo: { name: "Test" },
      }),
    ).toThrow();
  });

  it("passes with experience and valid dates", () => {
    expect(() =>
      validateResumeData({
        personalInfo: { name: "Test", email: "test@example.com" },
        experience: [
          {
            title: "Dev",
            company: "Corp",
            startDate: "2020-01",
            endDate: "Present",
          },
        ],
      }),
    ).not.toThrow();
  });

  it("throws on invalid date in experience", () => {
    expect(() =>
      validateResumeData({
        personalInfo: { name: "Test", email: "test@example.com" },
        experience: [
          {
            title: "Dev",
            company: "Corp",
            startDate: "January 2020",
            endDate: "Present",
          },
        ],
      }),
    ).toThrow();
  });
});

// ---------------------------------------------------------------------------
// ultraValidateAndNormalize
// ---------------------------------------------------------------------------

describe("ultraValidateAndNormalize", () => {
  it("normalizes and validates data", () => {
    const result = ultraValidateAndNormalize({
      personalInfo: { name: "  Test User  ", email: "test@example.com" },
    });
    expect(result).toBeDefined();
    expect(result.personalInfo).toBeDefined();
  });

  it("throws on invalid data (missing personalInfo)", () => {
    expect(() => ultraValidateAndNormalize({})).toThrow();
  });

  it("throws on missing name", () => {
    expect(() =>
      ultraValidateAndNormalize({
        personalInfo: { email: "test@example.com" },
      }),
    ).toThrow();
  });

  it("throws on missing email", () => {
    expect(() =>
      ultraValidateAndNormalize({
        personalInfo: { name: "Test" },
      }),
    ).toThrow();
  });

  it("normalizes email to lowercase", () => {
    const result = ultraValidateAndNormalize({
      personalInfo: { name: "Test", email: "TEST@Example.COM" },
    });
    const personalInfo = result.personalInfo as Record<string, unknown>;
    expect(personalInfo.email).toBe("test@example.com");
  });
});

// ---------------------------------------------------------------------------
// enhancedValidate
// ---------------------------------------------------------------------------

describe("enhancedValidate", () => {
  it("returns isValid true for valid data", () => {
    const result = enhancedValidate({
      personalInfo: { name: "Test", email: "test@example.com" },
    });
    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("returns isValid false when personalInfo missing", () => {
    const result = enhancedValidate({});
    expect(result.isValid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  it("adds warnings for URLs without protocol", () => {
    const result = enhancedValidate({
      personalInfo: {
        name: "Test",
        email: "test@example.com",
        website: "johndoe.dev",
      },
    });
    expect(result.isValid).toBe(true);
    expect(result.warnings.length).toBeGreaterThan(0);
    const personalInfo = result.normalizedData.personalInfo as Record<
      string,
      unknown
    >;
    expect(personalInfo.website).toBe("https://johndoe.dev");
  });

  it("includes metadata about validation level", () => {
    const result = enhancedValidate(
      {
        personalInfo: { name: "Test", email: "test@example.com" },
      },
      ValidationLevel.LENIENT,
    );
    expect(result.metadata).toHaveProperty("validationLevel", "lenient");
  });

  it("strict mode treats warnings as failures", () => {
    const result = enhancedValidate(
      {
        personalInfo: {
          name: "Test",
          email: "test@example.com",
          website: "johndoe.dev",
        },
      },
      ValidationLevel.STRICT,
    );
    // strict mode: isValid is false if there are ANY issues (warnings count)
    expect(result.isValid).toBe(false);
  });
});
