import { Hono } from "hono";
import type { Env } from "../types/env.js";
import { isCompilerCached } from "../engine/typst-compiler.js";

const app = new Hono<{ Bindings: Env }>();

app.get("/", (c) => {
  return c.json({
    message: "Welcome to Resume Engine Workers API",
    version: "2.0.0",
    engine: "Typst (WASM)",
    runtime: "Cloudflare Workers",
    documentation: "/docs",
    health_check: "/health",
    available_endpoints: {
      schemas: "/schema/:document_type",
      templates: "/templates",
      generation: "/generate",
      validation: "/validate",
      analysis: "/analyze",
      pdf_analysis: "/analyze-pdf",
    },
  });
});

app.get("/health", (c) => {
  return c.json({
    status: "healthy",
    typstCompilerCached: isCompilerCached(),
    timestamp: new Date().toISOString(),
  });
});

export default app;
