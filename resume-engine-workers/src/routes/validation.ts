import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import type { Env } from "../types/env.js";
import { ValidationRequestSchema } from "../schemas/requests.js";
import {
  validateResumeData,
  ultraValidateAndNormalize,
} from "../validation/validator.js";
import { ValidationError, InternalServerError } from "../errors/exceptions.js";

const app = new Hono<{ Bindings: Env }>();

app.post(
  "/validate",
  zValidator("json", ValidationRequestSchema),
  async (c) => {
    const request = c.req.valid("json");
    try {
      const dataDict = request.data;

      if (request.validation_level === "ultra") {
        try {
          const normalizedData = ultraValidateAndNormalize(dataDict);
          return c.json({
            valid: true,
            validation_level: "ultra",
            message: "Data successfully validated with ultra validation",
            data_summary: {
              document_type: request.document_type,
              sections_found: Object.keys(normalizedData),
              personal_info_complete:
                "personalInfo" in normalizedData &&
                "name" in
                  ((normalizedData.personalInfo as Record<string, unknown>) ??
                    {}) &&
                "email" in
                  ((normalizedData.personalInfo as Record<string, unknown>) ??
                    {}),
            },
          });
        } catch (e) {
          if (e instanceof ValidationError) {
            return c.json({
              valid: false,
              validation_level: "ultra",
              errors: [e.message],
              message: "Ultra validation failed. See errors for details.",
              suggestions: [
                "Fix the validation errors listed above",
                "Consider using standard validation if ultra validation is too strict",
              ],
            });
          }
          throw e;
        }
      } else {
        try {
          validateResumeData(dataDict);
          return c.json({
            valid: true,
            validation_level: "standard",
            message: "Data successfully validated with standard validation",
            data_summary: {
              document_type: request.document_type,
              sections_found: Object.keys(dataDict),
              personal_info_complete:
                "personalInfo" in dataDict &&
                "name" in
                  ((dataDict.personalInfo as Record<string, unknown>) ?? {}) &&
                "email" in
                  ((dataDict.personalInfo as Record<string, unknown>) ?? {}),
            },
          });
        } catch (e) {
          if (e instanceof ValidationError) {
            return c.json({
              valid: false,
              validation_level: "standard",
              errors: [e.message],
              message: "Standard validation failed. See errors for details.",
              suggestions: [
                "Fix the validation errors listed above",
                "Ensure personalInfo section includes name and email",
              ],
            });
          }
          throw e;
        }
      }
    } catch (e) {
      if (e instanceof ValidationError) throw e;
      throw new InternalServerError(`Validation error: ${String(e)}`);
    }
  },
);

export default app;
