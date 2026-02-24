/**
 * Custom Exception Hierarchy for Resume Engine Workers
 * Port of Python exceptions.py
 */

import {
  ErrorCode,
  ErrorCategory,
  ErrorSeverity,
  getErrorDefinition,
  formatErrorMessage,
} from "./error-codes.js";

export class ResumeEngineError extends Error {
  public readonly errorCode: ErrorCode;
  public readonly context: Record<string, unknown>;
  public readonly httpStatusCode: number;
  public readonly category: ErrorCategory;
  public readonly severity: ErrorSeverity;
  public readonly suggestedFix?: string;
  public readonly timestamp: string;

  constructor(
    errorCode: ErrorCode,
    context: Record<string, string> = {},
  ) {
    const def = getErrorDefinition(errorCode);
    const message = formatErrorMessage(errorCode, context);
    super(message);
    this.name = "ResumeEngineError";
    this.errorCode = errorCode;
    this.context = context;
    this.httpStatusCode = def?.httpStatusCode ?? 500;
    this.category = def?.category ?? ErrorCategory.SYSTEM;
    this.severity = def?.severity ?? ErrorSeverity.ERROR;
    this.suggestedFix = def?.suggestedFix;
    this.timestamp = new Date().toISOString();
  }

  toJSON() {
    return {
      error: {
        code: this.errorCode,
        category: this.category,
        severity: this.severity,
        title: getErrorDefinition(this.errorCode)?.title ?? "Error",
        message: this.message,
        suggestedFix: this.suggestedFix,
        timestamp: this.timestamp,
        ...(Object.keys(this.context).length > 0
          ? { context: this.context }
          : {}),
      },
    };
  }
}

// Validation Errors
export class ValidationError extends ResumeEngineError {
  public readonly fieldPath?: string;

  constructor(
    errorCode: ErrorCode,
    fieldPath?: string,
    context: Record<string, string> = {},
  ) {
    if (fieldPath) context.field = fieldPath;
    super(errorCode, context);
    this.name = "ValidationError";
    this.fieldPath = fieldPath;
  }
}

// Template Errors
export class TemplateError extends ResumeEngineError {
  public readonly templateName?: string;
  public readonly documentType?: string;

  constructor(
    errorCode: ErrorCode,
    templateName?: string,
    documentType?: string,
    context: Record<string, string> = {},
  ) {
    if (templateName) context.template = templateName;
    if (documentType) context.document_type = documentType;
    super(errorCode, context);
    this.name = "TemplateError";
    this.templateName = templateName;
    this.documentType = documentType;
  }
}

export class TemplateNotFoundError extends TemplateError {
  constructor(
    templateName: string,
    documentType: string,
    availableTemplates: string[] = [],
  ) {
    super(ErrorCode.TPL001, templateName, documentType, {
      available_templates: availableTemplates.join(", "),
    });
    this.name = "TemplateNotFoundError";
  }
}

export class TemplateCompilationError extends TemplateError {
  constructor(templateName: string, details: string) {
    super(ErrorCode.TPL002, templateName, undefined, { details });
    this.name = "TemplateCompilationError";
  }
}

export class TemplateRenderingError extends TemplateError {
  constructor(templateName: string, details: string) {
    super(ErrorCode.TPL003, templateName, undefined, { details });
    this.name = "TemplateRenderingError";
  }
}

export class TypstCompilationError extends TemplateError {
  constructor(details: string, templateName?: string) {
    super(ErrorCode.TPL007, templateName, undefined, { details });
    this.name = "TypstCompilationError";
  }
}

export class PDFGenerationError extends TemplateError {
  constructor(details: string, templateName?: string) {
    super(ErrorCode.TPL008, templateName, undefined, { details });
    this.name = "PDFGenerationError";
  }
}

// API Errors
export class APIError extends ResumeEngineError {
  constructor(errorCode: ErrorCode, context: Record<string, string> = {}) {
    super(errorCode, context);
    this.name = "APIError";
  }
}

export class InvalidRequestError extends APIError {
  constructor(details: string) {
    super(ErrorCode.API001, { details });
    this.name = "InvalidRequestError";
  }
}

export class InvalidParameterError extends APIError {
  constructor(parameter: string, value: string) {
    super(ErrorCode.API003, { parameter, value });
    this.name = "InvalidParameterError";
  }
}

export class ResourceNotFoundError extends APIError {
  constructor(resource: string) {
    super(ErrorCode.API011, { resource });
    this.name = "ResourceNotFoundError";
  }
}

export class RateLimitError extends APIError {
  constructor(retryAfter: number) {
    super(ErrorCode.API005, { retry_after: String(retryAfter) });
    this.name = "RateLimitError";
  }
}

// System Errors
export class InternalServerError extends ResumeEngineError {
  constructor(details: string) {
    super(ErrorCode.SYS001, { details });
    this.name = "InternalServerError";
  }
}

export class DependencyError extends ResumeEngineError {
  constructor(dependency: string) {
    super(ErrorCode.SYS006, { dependency });
    this.name = "DependencyError";
  }
}
