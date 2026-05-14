/**
 * edge-api — Cloudflare Workers entry point.
 *
 * Lab 17 (DevOps Core). All routes return JSON and use only platform bindings
 * (vars, secrets, KV) wired from `wrangler.jsonc`.
 */

export interface Env {
  // Plaintext vars from wrangler.jsonc (Task 4.1).
  APP_NAME: string;
  COURSE_NAME: string;

  // Secrets injected via `wrangler secret put` or .dev.vars (Task 4.2).
  // Optional in the type so local dev without secrets does not break /info.
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;

  // Workers KV namespace (Task 4.3).
  SETTINGS: KVNamespace;
}

const APP_VERSION = "1.0.0";
const STARTED_AT = new Date().toISOString();

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status: init.status ?? 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...(init.headers ?? {}),
    },
  });
}

// Returns "present" / "missing" without ever echoing the real value.
function maskSecret(value: string | undefined): string {
  if (!value) return "missing";
  return `present (${value.length} chars)`;
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Task 5.1: structured log line, visible via `wrangler tail` and in the
    // dashboard Logs panel when observability is enabled.
    console.log(
      "request",
      JSON.stringify({
        method: request.method,
        path: url.pathname,
        colo: request.cf?.colo,
        country: request.cf?.country,
      }),
    );

    switch (url.pathname) {
      case "/":
        return jsonResponse({
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          version: APP_VERSION,
          message: "Hello from Cloudflare Workers (edge-api).",
          routes: ["/", "/health", "/edge", "/info", "/counter"],
          startedAt: STARTED_AT,
          now: new Date().toISOString(),
        });

      case "/health":
        return jsonResponse({ status: "ok" });

      case "/edge": {
        // Task 3.1: surface request metadata Cloudflare attaches at the edge.
        // `request.cf` is undefined in local `wrangler dev` against a non-Cloudflare
        // listener, so we fall back gracefully.
        const cf = request.cf;
        return jsonResponse({
          colo: cf?.colo ?? "local-dev",
          country: cf?.country ?? "local-dev",
          city: cf?.city ?? null,
          region: cf?.region ?? null,
          asn: cf?.asn ?? null,
          asOrganization: cf?.asOrganization ?? null,
          httpProtocol: cf?.httpProtocol ?? null,
          tlsVersion: cf?.tlsVersion ?? null,
          timezone: cf?.timezone ?? null,
          clientAcceptEncoding: request.headers.get("accept-encoding"),
          observedAt: new Date().toISOString(),
        });
      }

      case "/info":
        // Task 4.1 (use plaintext var) + Task 4.2 (prove secrets are wired).
        return jsonResponse({
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          version: APP_VERSION,
          secrets: {
            API_TOKEN: maskSecret(env.API_TOKEN),
            ADMIN_EMAIL: maskSecret(env.ADMIN_EMAIL),
          },
          note: "Plaintext vars (APP_NAME, COURSE_NAME) live in wrangler.jsonc and are safe to commit. Secrets are injected via `wrangler secret put` and are never echoed.",
        });

      case "/counter": {
        // Task 4.3 + 4.4: KV-backed counter that survives redeploys.
        const raw = await env.SETTINGS.get("visits");
        const previous = Number(raw ?? "0");
        const visits = Number.isFinite(previous) ? previous + 1 : 1;
        await env.SETTINGS.put("visits", String(visits));
        return jsonResponse({
          key: "visits",
          visits,
          previous,
          persistedIn: "Workers KV (binding SETTINGS)",
        });
      }

      default:
        return jsonResponse(
          {
            error: "Not Found",
            path: url.pathname,
            knownRoutes: ["/", "/health", "/edge", "/info", "/counter"],
          },
          { status: 404 },
        );
    }
  },
} satisfies ExportedHandler<Env>;
