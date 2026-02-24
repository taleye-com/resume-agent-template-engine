/**
 * Abstract base interface for all templates.
 * Port of Python's TemplateInterface.
 */
export interface TemplateHelper {
  /** Validate the data against template requirements */
  validateData(): void;

  /** Render the template to Typst markup string */
  render(): string;

  /** List of required top-level data fields */
  readonly requiredFields: string[];

  /** The document type this template handles */
  readonly templateType: "resume" | "cover_letter";

  /** Optional: analyze document content for page optimization */
  analyzeDocument?(): Record<string, unknown>;
}

/**
 * Constructor type for template helpers.
 * Each template helper takes data + optional config.
 */
export type TemplateHelperConstructor = new (
  data: Record<string, unknown>,
  config?: Record<string, unknown>,
) => TemplateHelper;
