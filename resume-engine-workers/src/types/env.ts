export interface Env {
  // KV namespace for PDF/document caching
  DOCUMENT_CACHE: KVNamespace;

  // R2 bucket for Typst WASM binary and fonts
  TYPST_ASSETS: R2Bucket;

  // Environment variables
  ENVIRONMENT: string;
  CACHE_TTL_SECONDS: string;
  MAX_PDF_SIZE_BYTES: string;
}
