/**
 * Enhanced validation system for resume data.
 * Port of Python validation.py
 */

import { ErrorCode, ErrorSeverity } from "../errors/error-codes.js";
import { ValidationError } from "../errors/exceptions.js";

export enum ValidationLevel {
  STRICT = "strict",
  LENIENT = "lenient",
  PERMISSIVE = "permissive",
}

export interface ValidationIssue {
  fieldPath: string;
  errorCode: ErrorCode;
  message: string;
  severity: ErrorSeverity;
  suggestedFix?: string;
  originalValue?: unknown;
  correctedValue?: unknown;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  normalizedData: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

/**
 * Validate date format: YYYY-MM, YYYY-MM-DD, MM-YYYY, MM-DD-YYYY
 */
export function validateDateFormat(dateStr: string): boolean {
  if (!dateStr || dateStr.toLowerCase() === "present") return true;
  return /^(\d{4}-\d{1,2}(-\d{1,2})?|\d{1,2}-\d{4}|\d{1,2}-\d{1,2}-\d{4})$/.test(
    dateStr,
  );
}

/**
 * Normalize field names to match expected schema.
 */
function normalizeFieldNames(
  data: Record<string, unknown>,
): Record<string, unknown> {
  if (
    data.experience &&
    Array.isArray(data.experience)
  ) {
    for (const exp of data.experience as Record<string, unknown>[]) {
      if ("title" in exp && !("position" in exp)) {
        exp.position = exp.title;
      }
    }
  }
  return data;
}

/**
 * Standard validation — checks required fields and date formats.
 */
export function validateResumeData(
  data: Record<string, unknown>,
): void {
  if (!data.personalInfo) {
    throw new ValidationError(ErrorCode.VAL001, "personalInfo", {
      section: "root",
    });
  }

  const normalizedData = normalizeFieldNames(data);
  const personalInfo = normalizedData.personalInfo as Record<string, unknown>;

  if (!personalInfo.name) {
    throw new ValidationError(ErrorCode.VAL001, "personalInfo.name", {
      section: "personalInfo",
    });
  }
  if (!personalInfo.email) {
    throw new ValidationError(ErrorCode.VAL001, "personalInfo.email", {
      section: "personalInfo",
    });
  }

  // Validate dates in experience
  if (Array.isArray(normalizedData.experience)) {
    for (let i = 0; i < normalizedData.experience.length; i++) {
      const exp = normalizedData.experience[i] as Record<string, unknown>;
      for (const field of ["startDate", "endDate"]) {
        const val = exp[field] as string | undefined;
        if (val && val !== "Present" && !validateDateFormat(val)) {
          throw new ValidationError(
            ErrorCode.VAL006,
            `experience[${i}].${field}`,
            { date: val },
          );
        }
      }
    }
  }

  // Validate dates in education
  if (Array.isArray(normalizedData.education)) {
    for (let i = 0; i < normalizedData.education.length; i++) {
      const edu = normalizedData.education[i] as Record<string, unknown>;
      for (const field of ["startDate", "endDate", "graduationDate"]) {
        const val = edu[field] as string | undefined;
        if (val && val !== "Present" && !validateDateFormat(val)) {
          throw new ValidationError(
            ErrorCode.VAL006,
            `education[${i}].${field}`,
            { date: val },
          );
        }
      }
    }
  }
}

/**
 * Ultra validation with normalization and sanitization.
 */
export function ultraValidateAndNormalize(
  data: Record<string, unknown>,
): Record<string, unknown> {
  const result = enhancedValidate(data, ValidationLevel.LENIENT);

  if (!result.isValid) {
    const errorMessages = result.errors.map((e) =>
      e.suggestedFix
        ? `${e.fieldPath}: ${e.message}. ${e.suggestedFix}`
        : `${e.fieldPath}: ${e.message}`,
    );
    throw new ValidationError(ErrorCode.VAL010, "data", {
      details: errorMessages.join("\n"),
    });
  }

  return result.normalizedData;
}

/**
 * Enhanced validation with normalization.
 */
export function enhancedValidate(
  data: Record<string, unknown>,
  level: ValidationLevel = ValidationLevel.LENIENT,
): ValidationResult {
  const errors: ValidationIssue[] = [];
  const warnings: ValidationIssue[] = [];

  // Deep clone
  const workingData = JSON.parse(JSON.stringify(data)) as Record<
    string,
    unknown
  >;

  // Check required fields
  if (!workingData.personalInfo) {
    errors.push({
      fieldPath: "personalInfo",
      errorCode: ErrorCode.VAL001,
      message: "personalInfo section is required",
      severity: ErrorSeverity.ERROR,
      suggestedFix: "Add personalInfo object with at least name and email",
    });
    return {
      isValid: false,
      errors,
      warnings,
      normalizedData: workingData,
      metadata: { validationLevel: level },
    };
  }

  const personalInfo = workingData.personalInfo as Record<string, unknown>;
  if (!personalInfo.name) {
    errors.push({
      fieldPath: "personalInfo.name",
      errorCode: ErrorCode.VAL001,
      message: "name is required in personalInfo",
      severity: ErrorSeverity.ERROR,
      suggestedFix: "Add name field to personalInfo",
    });
  }
  if (!personalInfo.email) {
    errors.push({
      fieldPath: "personalInfo.email",
      errorCode: ErrorCode.VAL001,
      message: "email is required in personalInfo",
      severity: ErrorSeverity.ERROR,
      suggestedFix: "Add email field to personalInfo",
    });
  }

  // Normalize email
  if (typeof personalInfo.email === "string") {
    const normalized = personalInfo.email.trim().toLowerCase();
    if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(normalized)) {
      errors.push({
        fieldPath: "personalInfo.email",
        errorCode: ErrorCode.VAL003,
        message: `Invalid email format: '${personalInfo.email}'`,
        severity: ErrorSeverity.ERROR,
        suggestedFix: "Use format like 'user@domain.com'",
      });
    } else {
      personalInfo.email = normalized;
    }
  }

  // Normalize URLs
  for (const urlField of ["website", "linkedin", "github"]) {
    const val = personalInfo[urlField] as string | undefined;
    if (val && typeof val === "string") {
      if (!/^https?:\/\//.test(val)) {
        personalInfo[urlField] = `https://${val}`;
        warnings.push({
          fieldPath: `personalInfo.${urlField}`,
          errorCode: ErrorCode.VAL005,
          message: "Added https:// protocol to URL",
          severity: ErrorSeverity.INFO,
          originalValue: val,
          correctedValue: personalInfo[urlField],
        });
      }
    }
  }

  const isValid =
    level === ValidationLevel.STRICT
      ? errors.length === 0 && warnings.length === 0
      : errors.length === 0;

  return {
    isValid,
    errors,
    warnings,
    normalizedData: workingData,
    metadata: {
      validationLevel: level,
      totalIssues: errors.length + warnings.length,
      normalizationApplied: true,
    },
  };
}
