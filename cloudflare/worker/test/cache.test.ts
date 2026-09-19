import assert from "node:assert/strict";
import { test } from "vite-plus/test";

import { canonicalUrl, isCacheable, isStorable } from "../src/cache.ts";

const host = "https://ghcr-badge.egpl.dev";

test("the same badge with its parameters in another order shares one key", () => {
  const a = canonicalUrl(new URL(`${host}/eggplants/ghcr-badge/tags?trim=major&color=red&n=5`));
  const b = canonicalUrl(new URL(`${host}/eggplants/ghcr-badge/tags?n=5&color=red&trim=major`));
  assert.equal(a, b);
  assert.equal(a, `${host}/eggplants/ghcr-badge/tags?color=red&n=5&trim=major`);
});

test("different parameters are different badges", () => {
  const a = canonicalUrl(new URL(`${host}/eggplants/ghcr-badge/tags?n=3`));
  const b = canonicalUrl(new URL(`${host}/eggplants/ghcr-badge/tags?n=5`));
  const c = canonicalUrl(new URL(`${host}/eggplants/ghcr-badge/tags`));
  assert.notEqual(a, b);
  assert.notEqual(a, c);
});

test("repository-scoped package names keep their slashes", () => {
  assert.equal(
    canonicalUrl(new URL(`${host}/henrygd/beszel/beszel/tags`)),
    `${host}/henrygd/beszel/beszel/tags`,
  );
});

test("the key stays on the request's own origin", () => {
  assert.ok(
    canonicalUrl(new URL("https://other.example/x/y/size")).startsWith("https://other.example/"),
  );
});

test("everything but the health check is cacheable", () => {
  assert.equal(isCacheable("/health"), false);
  for (const path of ["/", "/index.html", "/static/style.css", "/eggplants/ghcr-badge/size"]) {
    assert.equal(isCacheable(path), true, path);
  }
});

test("only successful non-JSON answers are stored", () => {
  assert.equal(isStorable(200, "image/svg+xml"), true);
  assert.equal(isStorable(200, "image/svg+xml; charset=utf-8"), true);
  assert.equal(isStorable(200, "text/html; charset=utf-8"), true);
  // The server reports a missing package or a ghcr.io error as 200 JSON.
  assert.equal(isStorable(200, "application/json"), false);
  assert.equal(isStorable(200, "Application/JSON; charset=utf-8"), false);
  assert.equal(isStorable(200, null), false);
  assert.equal(isStorable(404, "image/svg+xml"), false);
  assert.equal(isStorable(500, "text/html"), false);
});
