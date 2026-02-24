import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import type { Env } from "../types/env.js";
import { AnalyzeRequestSchema } from "../schemas/requests.js";
import { getTemplateHelper } from "../engine/template-registry.js";
import { validateResumeData } from "../validation/validator.js";
import {
  TemplateNotFoundError,
  InternalServerError,
  ResumeEngineError,
} from "../errors/exceptions.js";
import { getAvailableTemplates } from "../engine/template-registry.js";

const app = new Hono<{ Bindings: Env }>();

app.post(
  "/analyze",
  zValidator("json", AnalyzeRequestSchema),
  async (c) => {
    const request = c.req.valid("json");
    try {
      validateResumeData(request.data);

      const HelperClass = getTemplateHelper(
        request.document_type,
        request.template,
      );
      if (!HelperClass) {
        throw new TemplateNotFoundError(
          request.template,
          request.document_type,
          Object.keys(
            getAvailableTemplates()[request.document_type] ?? {},
          ),
        );
      }

      const config = { spacing_mode: request.spacing_mode };
      const analysisData = { ...request.data, spacing_mode: request.spacing_mode };
      const helper = new HelperClass(analysisData, config);

      if (helper.analyzeDocument) {
        const analysis = helper.analyzeDocument();
        return c.json({
          success: true,
          document_type: request.document_type,
          template: request.template,
          analysis,
          tips: [
            "Use 'compact' mode to fit more content (default)",
            "Use 'ultra-compact' mode for maximum density (may reduce readability)",
            "Use 'normal' mode for best readability (requires more space)",
            "Aim for 600-700 words for 1-page resumes",
            "Aim for 1000-1200 words for 2-page resumes",
          ],
        });
      }

      return c.json({
        success: false,
        message: `Template '${request.template}' does not support content analysis yet`,
        available_for: ["classic"],
      });
    } catch (e) {
      if (e instanceof ResumeEngineError) throw e;
      throw new InternalServerError(String(e));
    }
  },
);

app.post(
  "/analyze-pdf",
  zValidator("json", AnalyzeRequestSchema),
  async (c) => {
    const request = c.req.valid("json");
    try {
      validateResumeData(request.data);

      const HelperClass = getTemplateHelper(
        request.document_type,
        request.template,
      );
      if (!HelperClass) {
        throw new TemplateNotFoundError(
          request.template,
          request.document_type,
          Object.keys(
            getAvailableTemplates()[request.document_type] ?? {},
          ),
        );
      }

      const config = { spacing_mode: request.spacing_mode };
      const analysisData = { ...request.data, spacing_mode: request.spacing_mode };
      const helper = new HelperClass(analysisData, config);

      let contentAnalysis: Record<string, unknown> = {};
      if (helper.analyzeDocument) {
        contentAnalysis = helper.analyzeDocument();
      }

      const totalWords = ((contentAnalysis.total_metrics as Record<string, number>) ?? {}).total_words ?? 0;
      const totalChars = ((contentAnalysis.total_metrics as Record<string, number>) ?? {}).total_characters ?? 0;
      const estimatedPages = ((contentAnalysis.total_metrics as Record<string, number>) ?? {}).estimated_pages ?? 1;

      const wordsPerPage = estimatedPages > 0 ? totalWords / estimatedPages : totalWords;

      let whitespacePct: number;
      if (wordsPerPage < 400) {
        whitespacePct = Math.min(50, 40 + (400 - wordsPerPage) / 20);
      } else if (wordsPerPage < 600) {
        whitespacePct = 30 + (600 - wordsPerPage) / 10;
      } else {
        whitespacePct = Math.max(10, 30 - (wordsPerPage - 600) / 20);
      }

      const densityScore = Math.min(100, wordsPerPage / 6);

      let layoutQuality: string;
      let readability: string;
      if (whitespacePct > 35) {
        layoutQuality = "Excellent - Good balance of content and whitespace";
        readability = "High";
      } else if (whitespacePct > 25) {
        layoutQuality = "Good - Adequate whitespace for readability";
        readability = "Medium-High";
      } else if (whitespacePct > 15) {
        layoutQuality = "Fair - Could use more whitespace";
        readability = "Medium";
      } else {
        layoutQuality = "Dense - Consider reducing content or using larger spacing";
        readability = "Low";
      }

      const recommendations: { content: string[]; whitespace: string[]; optimization: string[] } = {
        content: (contentAnalysis.recommendations as string[]) ?? [],
        whitespace: [],
        optimization: [],
      };

      if (whitespacePct < 20) {
        recommendations.whitespace.push(
          "Consider switching to 'normal' spacing mode for more whitespace",
          "Reduce content by 10-15% to improve readability",
        );
      } else if (whitespacePct < 30) {
        recommendations.whitespace.push(
          "Good content density, but could benefit from slightly more whitespace",
        );
      } else {
        recommendations.whitespace.push(
          "Excellent whitespace distribution - good visual balance",
        );
      }

      if (estimatedPages > 2) {
        recommendations.optimization.push(
          "Document spans more than 2 pages - consider using ultra-compact mode",
        );
      }

      return c.json({
        success: true,
        document_type: request.document_type,
        template: request.template,
        spacing_mode: request.spacing_mode,
        whitespace_analysis: {
          whitespace_percentage: Math.round(whitespacePct * 100) / 100,
          content_percentage: Math.round((100 - whitespacePct) * 100) / 100,
          layout_quality: layoutQuality,
          readability_score: readability,
          words_per_page: Math.round(wordsPerPage * 100) / 100,
          density_score: Math.round(densityScore * 100) / 100,
        },
        content_metrics: {
          total_words: totalWords,
          total_characters: totalChars,
          estimated_pages: estimatedPages,
          sections_count: ((contentAnalysis.section_analysis as unknown[]) ?? []).length,
        },
        spacing_configuration: {
          mode: request.spacing_mode,
        },
        section_analysis: contentAnalysis.section_analysis ?? [],
        recommendations,
        tips: [
          `Current layout uses approximately ${Math.round(whitespacePct * 10) / 10}% whitespace`,
          `Content density: ${Math.round(densityScore * 10) / 10}/100 (lower is more readable)`,
          "Use 'compact' for best balance of content and readability",
          "Aim for 30-40% whitespace for optimal readability",
        ],
      });
    } catch (e) {
      if (e instanceof ResumeEngineError) throw e;
      throw new InternalServerError(String(e));
    }
  },
);

export default app;
