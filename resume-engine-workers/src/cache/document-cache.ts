/**
 * KV-based document cache — port of Redis DocumentCache.
 * Uses SHA-256 hash of input for deterministic cache keys.
 */

import type { Env } from "../types/env.js";

const PDF_PREFIX = "pdf";
const TYPST_PREFIX = "typst";

async function sha256(input: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hash = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(hash);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function buildCacheKey(
  prefix: string,
  documentType: string,
  templateName: string,
  hash: string,
): string {
  return `${prefix}:${documentType}:${templateName}:${hash}`;
}

export class DocumentCache {
  private env: Env;
  private ttl: number;
  private hits = 0;
  private misses = 0;

  constructor(env: Env) {
    this.env = env;
    this.ttl = parseInt(env.CACHE_TTL_SECONDS ?? "86400", 10);
  }

  async getCacheKey(
    documentType: string,
    templateName: string,
    data: Record<string, unknown>,
    format: string,
  ): Promise<string> {
    const input = JSON.stringify({ documentType, templateName, data, format });
    const hash = await sha256(input);
    return buildCacheKey(
      format === "pdf" ? PDF_PREFIX : TYPST_PREFIX,
      documentType,
      templateName,
      hash,
    );
  }

  async getPdf(key: string): Promise<ArrayBuffer | null> {
    const result = await this.env.DOCUMENT_CACHE.get(key, "arrayBuffer");
    if (result) {
      this.hits++;
      return result;
    }
    this.misses++;
    return null;
  }

  async setPdf(key: string, pdfBytes: Uint8Array): Promise<void> {
    await this.env.DOCUMENT_CACHE.put(key, pdfBytes, {
      expirationTtl: this.ttl,
    });
  }

  async getTypst(key: string): Promise<string | null> {
    const result = await this.env.DOCUMENT_CACHE.get(key, "text");
    if (result) {
      this.hits++;
      return result;
    }
    this.misses++;
    return null;
  }

  async setTypst(key: string, source: string): Promise<void> {
    await this.env.DOCUMENT_CACHE.put(key, source, {
      expirationTtl: Math.floor(this.ttl / 2), // 12h for typst source
    });
  }

  async invalidate(key: string): Promise<void> {
    await this.env.DOCUMENT_CACHE.delete(key);
  }

  getMetrics() {
    const total = this.hits + this.misses;
    return {
      hits: this.hits,
      misses: this.misses,
      hitRate: total > 0 ? this.hits / total : 0,
      total,
    };
  }
}
