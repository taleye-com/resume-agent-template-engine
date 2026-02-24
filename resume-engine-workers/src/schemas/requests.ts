import { z } from "zod";

export const DocumentTypeEnum = z.enum(["resume", "cover_letter"]);
export type DocumentType = z.infer<typeof DocumentTypeEnum>;

export const OutputFormatEnum = z.enum(["pdf", "typst", "docx"]);

export const DocumentRequestSchema = z.object({
  document_type: DocumentTypeEnum,
  template: z.string().min(1),
  format: OutputFormatEnum.default("pdf"),
  data: z.record(z.any()),
  ultra_validation: z.boolean().default(false),
  spacing_mode: z.string().default("compact"),
});

export type DocumentRequest = z.infer<typeof DocumentRequestSchema>;

export const YAMLDocumentRequestSchema = z.object({
  document_type: DocumentTypeEnum,
  template: z.string().min(1),
  format: OutputFormatEnum.default("pdf"),
  yaml_data: z.string().min(1),
  ultra_validation: z.boolean().default(false),
  spacing_mode: z.string().default("compact"),
});

export type YAMLDocumentRequest = z.infer<typeof YAMLDocumentRequestSchema>;

export const ValidationRequestSchema = z.object({
  document_type: DocumentTypeEnum,
  data: z.record(z.any()),
  validation_level: z.string().default("standard"),
});

export type ValidationRequest = z.infer<typeof ValidationRequestSchema>;

export const AnalyzeRequestSchema = z.object({
  document_type: DocumentTypeEnum,
  template: z.string().min(1),
  data: z.record(z.any()),
  spacing_mode: z.string().default("compact"),
});

export type AnalyzeRequest = z.infer<typeof AnalyzeRequestSchema>;
