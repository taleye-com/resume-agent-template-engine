/**
 * Centralized Error Registry for Resume Engine Workers
 * Port of Python errors.py
 */

export enum ErrorCategory {
  VALIDATION = "validation",
  TEMPLATE = "template",
  API = "api",
  SYSTEM = "system",
  SECURITY = "security",
  DATA = "data",
  FILE = "file",
}

export enum ErrorSeverity {
  CRITICAL = "critical",
  ERROR = "error",
  WARNING = "warning",
  INFO = "info",
}

export enum ErrorCode {
  // Validation Errors (VAL001-VAL099)
  VAL001 = "VAL001", // Missing required field
  VAL002 = "VAL002", // Invalid field type
  VAL003 = "VAL003", // Invalid email format
  VAL004 = "VAL004", // Invalid phone format
  VAL005 = "VAL005", // Invalid URL format
  VAL006 = "VAL006", // Invalid date format
  VAL007 = "VAL007", // Field value too long
  VAL008 = "VAL008", // Field value too short
  VAL009 = "VAL009", // Invalid enum value
  VAL010 = "VAL010", // Schema validation failed
  VAL011 = "VAL011", // Data normalization failed
  VAL012 = "VAL012", // Typst injection detected
  VAL013 = "VAL013", // Invalid JSON structure
  VAL014 = "VAL014", // Invalid YAML structure
  VAL015 = "VAL015", // Validation level not supported

  // Template Errors (TPL001-TPL099)
  TPL001 = "TPL001", // Template not found
  TPL002 = "TPL002", // Template compilation failed
  TPL003 = "TPL003", // Template rendering failed
  TPL004 = "TPL004", // Template file corrupted
  TPL005 = "TPL005", // Template class not found
  TPL006 = "TPL006", // Template dependency missing
  TPL007 = "TPL007", // Typst compilation failed
  TPL008 = "TPL008", // PDF generation failed
  TPL009 = "TPL009", // Template directory not found
  TPL010 = "TPL010", // Template metadata invalid
  TPL011 = "TPL011", // Template format not supported
  TPL012 = "TPL012", // Template placeholder unreplaced

  // API Errors (API001-API099)
  API001 = "API001", // Invalid request format
  API002 = "API002", // Missing request parameter
  API003 = "API003", // Invalid request parameter
  API004 = "API004", // Request timeout
  API005 = "API005", // Rate limit exceeded
  API006 = "API006", // Invalid content type
  API007 = "API007", // Request too large
  API008 = "API008", // Invalid HTTP method
  API009 = "API009", // Authentication required
  API010 = "API010", // Authorization failed
  API011 = "API011", // Resource not found
  API012 = "API012", // Conflict with existing resource
  API013 = "API013", // Service unavailable

  // System Errors (SYS001-SYS099)
  SYS001 = "SYS001", // Internal server error
  SYS002 = "SYS002", // Database connection failed
  SYS003 = "SYS003", // External service unavailable
  SYS004 = "SYS004", // Configuration error
  SYS005 = "SYS005", // Memory allocation failed
  SYS006 = "SYS006", // Dependency not found
  SYS007 = "SYS007", // Environment setup failed
  SYS008 = "SYS008", // Service initialization failed
  SYS009 = "SYS009", // Resource exhausted
  SYS010 = "SYS010", // Unexpected exception

  // Security Errors (SEC001-SEC099)
  SEC001 = "SEC001", // Malicious input detected
  SEC002 = "SEC002", // File path traversal attempt
  SEC003 = "SEC003", // Command injection attempt
  SEC004 = "SEC004", // Unsafe file operation
  SEC005 = "SEC005", // Invalid file type
  SEC006 = "SEC006", // File size limit exceeded
  SEC007 = "SEC007", // Suspicious pattern detected
}

export interface ErrorDefinition {
  code: ErrorCode;
  category: ErrorCategory;
  severity: ErrorSeverity;
  title: string;
  messageTemplate: string;
  suggestedFix?: string;
  httpStatusCode?: number;
  userFacing: boolean;
}

const ERROR_DEFINITIONS: Record<string, ErrorDefinition> = {
  // Validation Errors
  [ErrorCode.VAL001]: {
    code: ErrorCode.VAL001,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Required Field Missing",
    messageTemplate: "Required field '{field}' is missing from {section}",
    suggestedFix: "Add the required field to your data",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL002]: {
    code: ErrorCode.VAL002,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Invalid Field Type",
    messageTemplate:
      "Field '{field}' must be of type {expected_type}, got {actual_type}",
    suggestedFix: "Change the field to the correct data type",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL003]: {
    code: ErrorCode.VAL003,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Invalid Email Format",
    messageTemplate: "Email '{email}' is not in valid format",
    suggestedFix: "Use format like 'user@domain.com'",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL004]: {
    code: ErrorCode.VAL004,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.WARNING,
    title: "Invalid Phone Format",
    messageTemplate: "Phone number '{phone}' could not be normalized",
    suggestedFix:
      "Use format like '(555) 123-4567' or '+1 (555) 123-4567'",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL005]: {
    code: ErrorCode.VAL005,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.WARNING,
    title: "Invalid URL Format",
    messageTemplate: "URL '{url}' is not in valid format",
    suggestedFix: "Use format like 'https://domain.com'",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL006]: {
    code: ErrorCode.VAL006,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Invalid Date Format",
    messageTemplate: "Date '{date}' is not in valid format",
    suggestedFix: "Use format like 'YYYY-MM' or 'YYYY-MM-DD'",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL010]: {
    code: ErrorCode.VAL010,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Schema Validation Failed",
    messageTemplate: "Schema validation failed: {details}",
    suggestedFix: "Check your data against the schema",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL012]: {
    code: ErrorCode.VAL012,
    category: ErrorCategory.SECURITY,
    severity: ErrorSeverity.CRITICAL,
    title: "Typst Injection Detected",
    messageTemplate:
      "Dangerous Typst command detected in field '{field}': {command}",
    suggestedFix: "Remove unsafe commands from your input",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL013]: {
    code: ErrorCode.VAL013,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Invalid JSON Structure",
    messageTemplate: "JSON parsing failed: {details}",
    suggestedFix: "Check JSON syntax and structure",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.VAL014]: {
    code: ErrorCode.VAL014,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.ERROR,
    title: "Invalid YAML Structure",
    messageTemplate: "YAML parsing failed: {details}",
    suggestedFix: "Check YAML syntax and indentation",
    httpStatusCode: 400,
    userFacing: true,
  },

  // Template Errors
  [ErrorCode.TPL001]: {
    code: ErrorCode.TPL001,
    category: ErrorCategory.TEMPLATE,
    severity: ErrorSeverity.ERROR,
    title: "Template Not Found",
    messageTemplate:
      "Template '{template}' not found for document type '{document_type}'",
    suggestedFix:
      "Use one of the available templates: {available_templates}",
    httpStatusCode: 404,
    userFacing: true,
  },
  [ErrorCode.TPL002]: {
    code: ErrorCode.TPL002,
    category: ErrorCategory.TEMPLATE,
    severity: ErrorSeverity.ERROR,
    title: "Template Compilation Failed",
    messageTemplate: "Failed to compile template '{template}': {details}",
    suggestedFix: "Check template syntax and dependencies",
    httpStatusCode: 500,
    userFacing: true,
  },
  [ErrorCode.TPL003]: {
    code: ErrorCode.TPL003,
    category: ErrorCategory.TEMPLATE,
    severity: ErrorSeverity.ERROR,
    title: "Template Rendering Failed",
    messageTemplate: "Failed to render template '{template}': {details}",
    suggestedFix: "Check data compatibility with template requirements",
    httpStatusCode: 500,
    userFacing: true,
  },
  [ErrorCode.TPL007]: {
    code: ErrorCode.TPL007,
    category: ErrorCategory.TEMPLATE,
    severity: ErrorSeverity.ERROR,
    title: "Typst Compilation Failed",
    messageTemplate: "Typst compilation failed: {details}",
    suggestedFix: "Check template markup for syntax errors",
    httpStatusCode: 500,
    userFacing: true,
  },
  [ErrorCode.TPL008]: {
    code: ErrorCode.TPL008,
    category: ErrorCategory.TEMPLATE,
    severity: ErrorSeverity.ERROR,
    title: "PDF Generation Failed",
    messageTemplate: "Failed to generate PDF output: {details}",
    suggestedFix: "Check Typst compilation logs for errors",
    httpStatusCode: 500,
    userFacing: true,
  },

  // API Errors
  [ErrorCode.API001]: {
    code: ErrorCode.API001,
    category: ErrorCategory.API,
    severity: ErrorSeverity.ERROR,
    title: "Invalid Request Format",
    messageTemplate: "Request format is invalid: {details}",
    suggestedFix: "Check API documentation for correct request format",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.API003]: {
    code: ErrorCode.API003,
    category: ErrorCategory.API,
    severity: ErrorSeverity.ERROR,
    title: "Invalid Request Parameter",
    messageTemplate: "Parameter '{parameter}' has invalid value: {value}",
    suggestedFix: "Check parameter format and allowed values",
    httpStatusCode: 400,
    userFacing: true,
  },
  [ErrorCode.API005]: {
    code: ErrorCode.API005,
    category: ErrorCategory.API,
    severity: ErrorSeverity.ERROR,
    title: "Rate Limit Exceeded",
    messageTemplate: "Rate limit exceeded. Try again in {retry_after} seconds.",
    suggestedFix: "Wait before making more requests",
    httpStatusCode: 429,
    userFacing: true,
  },
  [ErrorCode.API011]: {
    code: ErrorCode.API011,
    category: ErrorCategory.API,
    severity: ErrorSeverity.ERROR,
    title: "Resource Not Found",
    messageTemplate: "Requested resource '{resource}' not found",
    suggestedFix: "Check the resource path and ensure it exists",
    httpStatusCode: 404,
    userFacing: true,
  },

  // System Errors
  [ErrorCode.SYS001]: {
    code: ErrorCode.SYS001,
    category: ErrorCategory.SYSTEM,
    severity: ErrorSeverity.CRITICAL,
    title: "Internal Server Error",
    messageTemplate: "An unexpected error occurred: {details}",
    suggestedFix:
      "Try again later or contact support if the problem persists",
    httpStatusCode: 500,
    userFacing: false,
  },
  [ErrorCode.SYS006]: {
    code: ErrorCode.SYS006,
    category: ErrorCategory.SYSTEM,
    severity: ErrorSeverity.CRITICAL,
    title: "Dependency Not Found",
    messageTemplate: "Required dependency '{dependency}' not found",
    suggestedFix: "Ensure all system dependencies are available",
    httpStatusCode: 500,
    userFacing: false,
  },
};

export function getErrorDefinition(
  code: ErrorCode,
): ErrorDefinition | undefined {
  return ERROR_DEFINITIONS[code];
}

export function formatErrorMessage(
  code: ErrorCode,
  params: Record<string, string> = {},
): string {
  const def = ERROR_DEFINITIONS[code];
  if (!def) return `Unknown error code: ${code}`;
  let msg = def.messageTemplate;
  for (const [key, value] of Object.entries(params)) {
    msg = msg.replace(`{${key}}`, value);
  }
  return msg;
}

export function getHttpStatusCode(code: ErrorCode): number {
  return ERROR_DEFINITIONS[code]?.httpStatusCode ?? 500;
}
