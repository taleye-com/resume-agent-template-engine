/**
 * Typst WASM Compiler — loads Typst from R2, compiles markup to PDF.
 *
 * The WASM binary (~27MB) is stored in R2 and loaded dynamically at runtime.
 * The initialized compiler is cached in the isolate's global scope so
 * subsequent requests skip the R2 load + WASM init (~1-2s cold, ~0ms warm).
 *
 * Uses @myriaddreamin/typst-ts-web-compiler for the WASM bindings.
 */

import type { Env } from "../types/env.js";
// @ts-expect-error -- no types for the internal .mjs glue
import initTypst, {
  TypstCompilerBuilder,
  // @ts-expect-error -- untyped
  type TypstCompiler as TypstCompilerType,
} from "@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler.mjs";

const WASM_KEY = "typst_ts_web_compiler_bg.wasm";
const FONT_KEYS = ["fonts/Charter.ttc"];

// Isolate-level cache — survives across requests in the same isolate
let cachedCompiler: InstanceType<typeof TypstCompilerType> | null = null;
let wasmInitialized = false;

/**
 * Get or create the Typst compiler, loading WASM + fonts from R2 on first call.
 */
async function getCompiler(env: Env): Promise<any> {
  if (cachedCompiler) return cachedCompiler;

  // 1. Load WASM from R2
  if (!wasmInitialized) {
    const wasmObj = await env.TYPST_ASSETS.get(WASM_KEY);
    if (!wasmObj) {
      throw new Error(
        `Typst WASM binary not found in R2 at key '${WASM_KEY}'. ` +
          "Upload it with: wrangler r2 object put typst-assets/" +
          WASM_KEY +
          " --file=node_modules/@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler_bg.wasm",
      );
    }

    const wasmBytes = await wasmObj.arrayBuffer();
    await initTypst(wasmBytes);
    wasmInitialized = true;
  }

  // 2. Build the compiler with fonts
  const builder = new TypstCompilerBuilder();
  builder.set_dummy_access_model();

  // Load fonts from R2
  for (const fontKey of FONT_KEYS) {
    const fontObj = await env.TYPST_ASSETS.get(fontKey);
    if (fontObj) {
      const fontBytes = new Uint8Array(await fontObj.arrayBuffer());
      await builder.add_raw_font(fontBytes);
    }
  }

  cachedCompiler = await builder.build();
  return cachedCompiler;
}

/**
 * Compile Typst markup source to PDF bytes.
 */
export async function compileTypst(
  source: string,
  env: Env,
): Promise<Uint8Array> {
  const compiler = await getCompiler(env);

  // Reset state from previous compile
  compiler.reset();

  // Add the source file
  compiler.add_source("/main.typ", source);

  // Compile to PDF (fmt="pdf", diagnostics_format=0)
  const result = compiler.compile("/main.typ", null, "pdf", 0);

  if (!result) {
    throw new Error("Typst compilation returned null — check your Typst markup for errors");
  }

  // The result should be a Uint8Array of PDF bytes
  if (result instanceof Uint8Array) {
    return result;
  }

  // Some versions return an object with result/diagnostics
  if (result.result) {
    return new Uint8Array(result.result);
  }

  throw new Error(
    `Unexpected Typst compile result type: ${typeof result}. ` +
      `Keys: ${result && typeof result === "object" ? Object.keys(result).join(", ") : "N/A"}`,
  );
}

/**
 * Check if the Typst compiler is ready (WASM initialized + compiler built).
 */
export function isCompilerCached(): boolean {
  return cachedCompiler !== null;
}

/**
 * Clear the isolate-level cache (useful for testing).
 */
export function clearCompilerCache(): void {
  if (cachedCompiler) {
    try {
      cachedCompiler.free();
    } catch {
      // ignore
    }
  }
  cachedCompiler = null;
  wasmInitialized = false;
}
