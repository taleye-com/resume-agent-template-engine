/**
 * Hardcoded template registry for CF Workers (no filesystem scanning).
 * Port of Python's TemplateRegistry.
 */
import type { TemplateHelperConstructor } from "./template-interface.js";
import { ClassicResumeHelper } from "../templates/resume/classic/helper.js";
import { TwoColumnResumeHelper } from "../templates/resume/two-column/helper.js";
import { ClassicCoverLetterHelper } from "../templates/cover-letter/classic/helper.js";
import { TwoColumnCoverLetterHelper } from "../templates/cover-letter/two-column/helper.js";

export interface TemplateInfo {
  name: string;
  documentType: string;
  helperClass: TemplateHelperConstructor;
  description: string;
  requiredFields: string[];
}

const TEMPLATE_REGISTRY: Record<string, Record<string, TemplateInfo>> = {
  resume: {
    classic: {
      name: "classic",
      documentType: "resume",
      helperClass: ClassicResumeHelper,
      description: "Clean, professional single-column resume template",
      requiredFields: ["personalInfo"],
    },
    two_column: {
      name: "two_column",
      documentType: "resume",
      helperClass: TwoColumnResumeHelper,
      description: "Professional two-column resume with sidebar",
      requiredFields: ["personalInfo"],
    },
  },
  cover_letter: {
    classic: {
      name: "classic",
      documentType: "cover_letter",
      helperClass: ClassicCoverLetterHelper,
      description: "Clean, professional cover letter template",
      requiredFields: ["personalInfo", "body"],
    },
    two_column: {
      name: "two_column",
      documentType: "cover_letter",
      helperClass: TwoColumnCoverLetterHelper,
      description: "Two-column cover letter with sidebar contact info",
      requiredFields: ["personalInfo", "body"],
    },
  },
};

export function getAvailableTemplates(
  documentType?: string,
): Record<string, string[]> {
  if (documentType) {
    const templates = TEMPLATE_REGISTRY[documentType];
    if (!templates) return {};
    return { [documentType]: Object.keys(templates) };
  }
  const result: Record<string, string[]> = {};
  for (const [docType, templates] of Object.entries(TEMPLATE_REGISTRY)) {
    result[docType] = Object.keys(templates);
  }
  return result;
}

export function getTemplateInfo(
  documentType: string,
  templateName: string,
): TemplateInfo | undefined {
  return TEMPLATE_REGISTRY[documentType]?.[templateName];
}

export function getTemplateHelper(
  documentType: string,
  templateName: string,
): TemplateHelperConstructor | undefined {
  return TEMPLATE_REGISTRY[documentType]?.[templateName]?.helperClass;
}
