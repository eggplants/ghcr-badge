/**
 * Cache policy for the badge gateway.
 *
 * A badge is a pure function of its URL — owner, package, endpoint and query
 * parameters — and the answer only changes when a new image is pushed to
 * ghcr.io, so the URL is the whole cache key. Query parameters are sorted so
 * that `?color=red&n=5` and `?n=5&color=red` share one entry.
 */

/**
 * Paths that must reach the container every time. `/health` is answered by the
 * Worker itself so a monitor never wakes the container; it is listed here so a
 * request for it can never be served stale should that change.
 */
const UNCACHEABLE_PATHS = new Set(["/health"]);

/** True when responses for this path may be stored in the edge cache. */
export function isCacheable(pathname: string): boolean {
  return !UNCACHEABLE_PATHS.has(pathname);
}

/**
 * The URL a response is stored under: the request's own origin (the Cache API
 * refuses to store under a host the zone does not own), the path as given, and
 * the query parameters in a canonical order.
 */
export function canonicalUrl(url: URL): string {
  const key = new URL(url.origin + url.pathname);
  const params = [...url.searchParams.entries()].sort(byEntry);
  for (const [name, value] of params) key.searchParams.append(name, value);
  return key.toString();
}

/**
 * A response is worth keeping only when it is the thing the client asked for.
 * The badge server answers upstream failures — a package that does not exist,
 * a ghcr.io rate limit — as `200 application/json` with an `exception` field,
 * and those must not be pinned to the cache for the whole TTL. The one
 * legitimate JSON answer, `/index.json`, is rare enough to pay for on every hit.
 */
export function isStorable(status: number, contentType: string | null): boolean {
  if (status !== 200) return false;
  const type = (contentType ?? "").split(";")[0]?.trim().toLowerCase() ?? "";
  return type !== "" && type !== "application/json";
}

function byEntry([aName, aValue]: [string, string], [bName, bValue]: [string, string]): number {
  return byCodeUnit(aName, bName) || byCodeUnit(aValue, bValue);
}

/** The default sort order, spelled out so the cache key stays locale-independent. */
function byCodeUnit(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}
