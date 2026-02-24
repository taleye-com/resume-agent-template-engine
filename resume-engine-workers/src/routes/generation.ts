import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import type { Env } from "../types/env.js";
import {
  DocumentRequestSchema,
  YAMLDocumentRequestSchema,
} from "../schemas/requests.js";
import { renderDocument } from "../engine/template-engine.js";
import { generateDocx } from "../docx/docx-generator.js";
import {
  validateResumeData,
  ultraValidateAndNormalize,
} from "../validation/validator.js";
import { parseYAML } from "../utils/yaml-parser.js";
import { DocumentCache } from "../cache/document-cache.js";
import {
  InvalidParameterError,
  InternalServerError,
  ResumeEngineError,
} from "../errors/exceptions.js";

const app = new Hono<{ Bindings: Env }>();

app.post(
  "/generate",
  zValidator("json", DocumentRequestSchema),
  async (c) => {
    const request = c.req.valid("json");

    try {
      // Validate
      let dataToUse: Record<string, unknown>;
      if (request.ultra_validation) {
        dataToUse = ultraValidateAndNormalize(request.data);
      } else {
        validateResumeData(request.data);
        dataToUse = request.data;
      }

      // Add spacing mode
      dataToUse.spacing_mode = request.spacing_mode;

      // Check format
      const format = request.format.toLowerCase();
      if (format !== "pdf" && format !== "typst" && format !== "docx") {
        throw new InvalidParameterError("format", request.format);
      }

      // DOCX path — no Typst/WASM needed
      if (format === "docx") {
        const result = await generateDocx(request.document_type, dataToUse);
        return new Response(result.docxBytes, {
          headers: {
            "Content-Type":
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Content-Disposition": `attachment; filename="${result.filename}"`,
          },
        });
      }

      // Check cache for PDF
      if (format === "pdf") {
        const cache = new DocumentCache(c.env);
        const cacheKey = await cache.getCacheKey(
          request.document_type,
          request.template,
          dataToUse,
          "pdf",
        );
        const cached = await cache.getPdf(cacheKey);
        if (cached) {
          const personName = (
            ((dataToUse.personalInfo as Record<string, unknown>)
              ?.name as string) ?? "output"
          ).replace(/\s+/g, "_");
          return new Response(cached, {
            headers: {
              "Content-Type": "application/pdf",
              "Content-Disposition": `attachment; filename="${request.document_type}_${personName}.pdf"`,
              "X-Cache": "HIT",
            },
          });
        }
      }

      // Render (pdf or typst)
      const result = await renderDocument(
        request.document_type,
        request.template,
        dataToUse,
        format,
        c.env,
      );

      if (format === "typst") {
        return c.text(result.typstSource, 200, {
          "Content-Type": "text/plain; charset=utf-8",
          "Content-Disposition": `attachment; filename="${result.filename}"`,
        });
      }

      // PDF response
      if (result.pdfBytes) {
        // Cache the PDF
        const cache = new DocumentCache(c.env);
        const cacheKey = await cache.getCacheKey(
          request.document_type,
          request.template,
          dataToUse,
          "pdf",
        );
        // Don't await cache write — fire and forget
        cache.setPdf(cacheKey, result.pdfBytes).catch(console.error);

        return new Response(result.pdfBytes, {
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `attachment; filename="${result.filename}"`,
            "X-Cache": "MISS",
          },
        });
      }

      throw new InternalServerError("PDF generation did not produce output");
    } catch (e) {
      if (e instanceof ResumeEngineError) throw e;
      throw new InternalServerError(String(e));
    }
  },
);

app.post(
  "/generate-yaml",
  zValidator("json", YAMLDocumentRequestSchema),
  async (c) => {
    const request = c.req.valid("json");

    try {
      // Parse YAML
      const data = parseYAML(request.yaml_data);

      // Validate
      let dataToUse: Record<string, unknown>;
      if (request.ultra_validation) {
        dataToUse = ultraValidateAndNormalize(data);
      } else {
        validateResumeData(data);
        dataToUse = data;
      }

      dataToUse.spacing_mode = request.spacing_mode;

      const format = request.format.toLowerCase();
      if (format !== "pdf" && format !== "typst" && format !== "docx") {
        throw new InvalidParameterError("format", request.format);
      }

      // DOCX path — no Typst/WASM needed
      if (format === "docx") {
        const result = await generateDocx(request.document_type, dataToUse);
        return new Response(result.docxBytes, {
          headers: {
            "Content-Type":
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Content-Disposition": `attachment; filename="${result.filename}"`,
          },
        });
      }

      const result = await renderDocument(
        request.document_type,
        request.template,
        dataToUse,
        format,
        c.env,
      );

      if (format === "typst") {
        return c.text(result.typstSource, 200, {
          "Content-Type": "text/plain; charset=utf-8",
          "Content-Disposition": `attachment; filename="${result.filename}"`,
        });
      }

      if (result.pdfBytes) {
        return new Response(result.pdfBytes, {
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `attachment; filename="${result.filename}"`,
          },
        });
      }

      throw new InternalServerError("PDF generation did not produce output");
    } catch (e) {
      if (e instanceof ResumeEngineError) throw e;
      throw new InternalServerError(String(e));
    }
  },
);

export default app;
