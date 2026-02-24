import { Container, getRandom } from "@cloudflare/containers";

interface Env {
  RESUME_ENGINE: DurableObjectNamespace<ResumeEngine>;
}

export class ResumeEngine extends Container {
  defaultPort = 8501;
  sleepAfter = "5m";

  override onStart(): void {
    console.log("Resume engine container started");
  }

  override onStop(): void {
    console.log("Resume engine container stopped");
  }

  override onError(error: unknown): void {
    console.error("Resume engine container error:", error);
    throw error;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      // Load balance across up to 3 container instances
      const container = await getRandom(env.RESUME_ENGINE, 3);
      return await container.fetch(request);
    } catch (err) {
      return new Response(
        JSON.stringify({
          error: "Service starting up, please retry in a few seconds",
          detail: err instanceof Error ? err.message : "Unknown error",
        }),
        {
          status: 503,
          headers: {
            "Content-Type": "application/json",
            "Retry-After": "10",
          },
        }
      );
    }
  },
};
