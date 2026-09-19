/**
 * Gateway for ghcr-badge on Cloudflare Containers.
 *
 * The Worker is the only public surface. It answers `/health` on its own,
 * serves badges and the landing page from the edge cache, rate limits the
 * misses per IP, and forwards those to the ghcr-badge container listening on
 * port 5000 (the `ghcr-badge-server` entrypoint of ../../Dockerfile).
 *
 * A badge only changes when a new image is pushed to ghcr.io, so caching by
 * URL is what keeps the container asleep: GitHub's Camo re-fetches every badge
 * in every README on every page view, and all of those are hits.
 */
import { Container, getContainer } from "@cloudflare/containers";
import type { StopParams } from "@cloudflare/containers";
import type { DurableObject } from "cloudflare:workers";

import { canonicalUrl, isCacheable, isStorable } from "./cache.ts";

/** Bindings and variables the Worker is deployed with; see ../../terraform/main.tf. */
export interface Env {
  GHCR_BADGE: DurableObjectNamespace<GhcrBadgeContainer>;
  RL_MISS?: RateLimit;
  APP_VERSION?: string;
  CONTAINER_SLEEP_AFTER?: string;
  CACHE_TTL?: string;
  BROWSER_TTL?: string;
}

/** The badge server; see ../../../Dockerfile and ../../../ghcr_badge/server.py. */
export class GhcrBadgeContainer extends Container<Env> {
  override defaultPort = 5000;
  override sleepAfter: string | number = "10m";

  constructor(ctx: DurableObject["ctx"], env: Env) {
    super(ctx, env);
    if (env.CONTAINER_SLEEP_AFTER) {
      this.sleepAfter = env.CONTAINER_SLEEP_AFTER;
    }
  }

  override onStart(): void {
    console.log("ghcr-badge: container started");
  }

  override onStop({ exitCode, reason }: StopParams): void {
    console.log(`ghcr-badge: container stopped (exit=${exitCode}, reason=${reason})`);
  }

  override onError(error: unknown): never {
    console.error("ghcr-badge: container error", error);
    throw error;
  }
}

/**
 * One instance is plenty: a badge costs the container a single call to ghcr.io,
 * and everything that repeats is a cache hit. The name is fixed so that every
 * miss lands on the same warm instance.
 */
const INSTANCE_NAME = "ghcr-badge-0";

const DEFAULTS = {
  CACHE_TTL: 600,
  BROWSER_TTL: 300,
};

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return fail(405, "method_not_allowed", "Use GET or HEAD.", { allow: "GET, HEAD" });
    }

    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return health(env);
    }
    if (url.pathname === "/robots.txt") {
      return robotsTxt();
    }

    const cache = caches.default;
    const cacheable = isCacheable(url.pathname);
    // The badge server has no request body to read and no header it acts on
    // (see ghcr_badge/server.py), so the cache key is the URL alone; and every
    // upstream call is a GET so that a HEAD can be answered from the same entry.
    const cacheKey = new Request(canonicalUrl(url), { method: "GET" });

    // The cache lookup comes before the rate limit on purpose: a hit costs no
    // container time, and Camo re-fetching a README's badges is exactly the
    // traffic this gateway exists to absorb.
    if (cacheable) {
      const hit = await cache.match(cacheKey);
      if (hit) {
        return reply(request, hit, { "x-cache": "HIT" });
      }
    }

    if (env.RL_MISS) {
      const clientIp = request.headers.get("cf-connecting-ip") ?? "unknown";
      const { success } = await env.RL_MISS.limit({ key: clientIp });
      if (!success) {
        return fail(429, "rate_limited", "Too many uncached requests.", { "retry-after": "60" });
      }
    }

    let upstream: Response;
    try {
      upstream = await forward(env, url);
    } catch (error) {
      console.error("ghcr-badge: upstream failure", error);
      return fail(502, "upstream_error", "The badge server did not answer in time.");
    }

    if (!cacheable || !isStorable(upstream.status, upstream.headers.get("content-type"))) {
      return reply(request, upstream, { "x-cache": "BYPASS", "cache-control": "no-store" });
    }

    const edgeTtl = num(env.CACHE_TTL, DEFAULTS.CACHE_TTL);
    const browserTtl = num(env.BROWSER_TTL, DEFAULTS.BROWSER_TTL);
    const storable = new Response(upstream.body, upstream);
    // The server sends `no-store` (so that Camo never keeps a badge for too
    // long); the Cache API honours that and would silently store nothing, so
    // the directive is replaced with the TTLs this deployment chooses.
    storable.headers.set(
      "cache-control",
      `public, max-age=${browserTtl}, s-maxage=${edgeTtl}, stale-while-revalidate=${edgeTtl}`,
    );
    storable.headers.delete("pragma");
    storable.headers.delete("expires");
    storable.headers.delete("set-cookie");

    ctx.waitUntil(cache.put(cacheKey, storable.clone()));
    return reply(request, storable, { "x-cache": "MISS" });
  },
};

/**
 * Answered by the Worker so that an uptime monitor never wakes the container.
 * The container's own `/health` is what its readiness check watches.
 */
function health(env: Env): Response {
  return new Response(JSON.stringify({ ok: true, version: env.APP_VERSION ?? null }), {
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

/**
 * Crawlers are welcome on the landing page and not on the badges: a crawler
 * walking badge URLs would spend container time on images nobody looks at.
 */
function robotsTxt(): Response {
  const body = ["User-agent: *", "Allow: /$", "Disallow: /", ""].join("\n");
  return new Response(body, {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=86400",
    },
  });
}

/**
 * Forwards the request to the container as a GET. Only the path and query
 * matter to the badge server; nothing from the client's headers is passed on.
 */
async function forward(env: Env, url: URL): Promise<Response> {
  const target = new URL(`http://ghcr-badge${url.pathname}${url.search}`);
  const container = getContainer(env.GHCR_BADGE, INSTANCE_NAME);
  return container.fetch(
    new Request(target.toString(), { method: "GET", headers: { accept: "*/*" } }),
  );
}

/**
 * Builds the response the client gets: the cached or upstream response with
 * the gateway's own headers on top, and no body when the client sent HEAD.
 */
function reply(request: Request, response: Response, extra: Record<string, string>): Response {
  const out = new Response(request.method === "HEAD" ? null : response.body, response);
  for (const [k, v] of Object.entries(extra)) {
    out.headers.set(k, v);
  }
  return out;
}

function fail(
  status: number,
  code: string,
  message: string,
  extra: Record<string, string> = {},
): Response {
  return new Response(JSON.stringify({ error: code, message }), {
    status,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      ...extra,
    },
  });
}

function num(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
