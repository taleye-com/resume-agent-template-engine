/**
 * Simple token-bucket rate limiter via KV.
 */

import type { Context, Next } from "hono";
import type { Env } from "../types/env.js";
import { RateLimitError } from "../errors/exceptions.js";

const MAX_REQUESTS = 60; // per window
const WINDOW_SECONDS = 60;

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

export async function rateLimiter(
  c: Context<{ Bindings: Env }>,
  next: Next,
): Promise<Response | void> {
  const ip =
    c.req.header("cf-connecting-ip") ??
    c.req.header("x-forwarded-for") ??
    "unknown";
  const key = `ratelimit:${ip}`;
  const now = Date.now();

  try {
    const stored = await c.env.DOCUMENT_CACHE.get(key, "text");
    let entry: RateLimitEntry;

    if (stored) {
      entry = JSON.parse(stored);
      if (now > entry.resetAt) {
        // Window expired, reset
        entry = { count: 1, resetAt: now + WINDOW_SECONDS * 1000 };
      } else {
        entry.count++;
      }
    } else {
      entry = { count: 1, resetAt: now + WINDOW_SECONDS * 1000 };
    }

    if (entry.count > MAX_REQUESTS) {
      const retryAfter = Math.ceil((entry.resetAt - now) / 1000);
      throw new RateLimitError(retryAfter);
    }

    // Store updated count
    await c.env.DOCUMENT_CACHE.put(key, JSON.stringify(entry), {
      expirationTtl: WINDOW_SECONDS,
    });

    // Set rate limit headers
    c.header("X-RateLimit-Limit", String(MAX_REQUESTS));
    c.header("X-RateLimit-Remaining", String(MAX_REQUESTS - entry.count));
    c.header("X-RateLimit-Reset", String(Math.ceil(entry.resetAt / 1000)));
  } catch (e) {
    if (e instanceof RateLimitError) throw e;
    // If KV fails, allow the request (fail open)
    console.error("Rate limiter KV error:", e);
  }

  await next();
}
