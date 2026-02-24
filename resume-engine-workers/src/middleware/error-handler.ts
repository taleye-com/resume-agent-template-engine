/**
 * Global error handler middleware for Hono.
 */

import type { Context } from "hono";
import { ResumeEngineError } from "../errors/exceptions.js";

export function handleError(err: Error, c: Context): Response {
  if (err instanceof ResumeEngineError) {
    return c.json(err.toJSON(), err.httpStatusCode as 400 | 404 | 500);
  }

  // Unknown error
  console.error("Unexpected error:", err);
  return c.json(
    {
      error: {
        code: "SYS001",
        category: "system",
        severity: "critical",
        title: "Internal Server Error",
        message: "An unexpected error occurred",
        timestamp: new Date().toISOString(),
      },
    },
    500,
  );
}
