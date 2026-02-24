/**
 * Resume Engine Workers — Main entry point.
 *
 * Hono.js application deployed on Cloudflare Workers.
 * Composes all route modules, applies middleware, and exports the CF Worker fetch handler.
 */

import { Hono } from "hono";
import { cors } from "hono/cors";
import type { Env } from "./types/env.js";
import { handleError } from "./middleware/error-handler.js";
import { rateLimiter } from "./middleware/rate-limiter.js";

// Route modules
import generalRoutes from "./routes/general.js";
import templateRoutes from "./routes/templates.js";
import schemaRoutes from "./routes/schema.js";
import validationRoutes from "./routes/validation.js";
import generationRoutes from "./routes/generation.js";
import analysisRoutes from "./routes/analysis.js";

const app = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Global middleware
// ---------------------------------------------------------------------------

// CORS
app.use(
  "*",
  cors({
    origin: "*",
    allowMethods: ["GET", "POST", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
    maxAge: 86400,
  }),
);

// Rate limiter (token-bucket via KV)
app.use("*", rateLimiter);

// Global error handler
app.onError(handleError);

// ---------------------------------------------------------------------------
// Mount routes
// ---------------------------------------------------------------------------

app.route("/", generalRoutes);
app.route("/", templateRoutes);
app.route("/", schemaRoutes);
app.route("/", validationRoutes);
app.route("/", generationRoutes);
app.route("/", analysisRoutes);

// ---------------------------------------------------------------------------
// CF Worker export
// ---------------------------------------------------------------------------

export default app;
