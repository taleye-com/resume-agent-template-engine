/**
 * Central Template Engine — orchestrates validate -> render -> compile.
 * Port of Python's TemplateEngine.
 */

import type { Env } from "../types/env.js";
import type { TemplateHelper } from "./template-interface.js";
import {
  getAvailableTemplates,
  getTemplateHelper,
  getTemplateInfo,
} from "./template-registry.js";
import { compileTypst } from "./typst-compiler.js";
import {
  TemplateNotFoundError,
  TemplateRenderingError,
  InvalidParameterError,
} from "../errors/exceptions.js";

export interface RenderResult {
  /** Typst markup source */
  typstSource: string;
  /** PDF bytes (only if format is pdf) */
  pdfBytes?: Uint8Array;
  /** Output format */
  format: string;
  /** Suggested filename */
  filename: string;
}

/**
 * Render a document from data to Typst source + optionally compile to PDF.
 */
export async function renderDocument(
  documentType: string,
  templateName: string,
  data: Record<string, unknown>,
  format: string = "pdf",
  env?: Env,
): Promise<RenderResult> {
  // Validate document type
  const allTemplates = getAvailableTemplates();
  if (!(documentType in allTemplates)) {
    throw new InvalidParameterError(
      "document_type",
      documentType,
    );
  }

  // Validate template exists
  const HelperClass = getTemplateHelper(documentType, templateName);
  if (!HelperClass) {
    throw new TemplateNotFoundError(
      templateName,
      documentType,
      allTemplates[documentType] ?? [],
    );
  }

  // Create template instance
  const config: Record<string, unknown> = {};
  if (data.spacing_mode) config.spacing_mode = data.spacing_mode;
  if (data.spacingMode) config.spacing_mode = data.spacingMode;

  const helper: TemplateHelper = new HelperClass(data, config);

  // Validate data
  helper.validateData();

  // Render to Typst markup
  let typstSource: string;
  try {
    typstSource = helper.render();
  } catch (e) {
    if (e instanceof Error) {
      throw new TemplateRenderingError(templateName, e.message);
    }
    throw new TemplateRenderingError(templateName, String(e));
  }

  // Determine filename
  const personName = (
    (data.personalInfo as Record<string, unknown>)?.name as string ?? "output"
  ).replace(/\s+/g, "_");
  const ext = format === "typst" ? "typ" : format;
  const filename = `${documentType}_${personName}.${ext}`;

  const result: RenderResult = { typstSource, format, filename };

  // Compile to PDF if requested
  if (format === "pdf" && env) {
    result.pdfBytes = await compileTypst(typstSource, env);
  }

  return result;
}

/**
 * Get metadata about a specific template.
 */
export function getTemplateMetadata(
  documentType: string,
  templateName: string,
): Record<string, unknown> {
  const info = getTemplateInfo(documentType, templateName);
  if (!info) {
    throw new TemplateNotFoundError(
      templateName,
      documentType,
      Object.keys(getAvailableTemplates()[documentType] ?? {}),
    );
  }

  return {
    name: info.name,
    documentType: info.documentType,
    description: info.description,
    requiredFields: info.requiredFields,
  };
}
