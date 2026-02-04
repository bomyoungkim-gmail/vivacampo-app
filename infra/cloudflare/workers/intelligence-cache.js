/**
 * VivaCampo Intelligence Cache Worker
 *
 * Caches nitrogen/correlation endpoints for 1 hour.
 * Endpoints:
 * - /v1/app/aois/{id}/nitrogen/status
 * - /v1/app/aois/{id}/correlation/*
 *
 * Environment Variables:
 * - ORIGIN_URL: API origin URL (e.g., https://api.vivacampo.com.br)
 */

const CACHE_TTL = 3600;

function isIntelligenceRequest(url) {
  return (
    url.pathname.includes('/nitrogen/') ||
    url.pathname.includes('/correlation/')
  );
}

function getCacheKey(request) {
  const url = new URL(request.url);
  const params = new URLSearchParams(url.searchParams);
  const sortedParams = new URLSearchParams([...params.entries()].sort());
  const cacheUrl = `${url.origin}${url.pathname}?${sortedParams.toString()}`;
  return new Request(cacheUrl, {
    method: 'GET',
    headers: request.headers,
  });
}

function addCacheHeaders(response, cacheStatus) {
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', `public, max-age=${CACHE_TTL}`);
  headers.set('CF-Cache-Status', cacheStatus);
  headers.set('X-Cache-TTL', CACHE_TTL.toString());
  headers.set('X-VivaCampo-Cache', 'intelligence-worker');
  headers.set('Vary', 'Accept-Encoding');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

async function handleRequest(request, env, ctx) {
  const cache = caches.default;
  const cacheKey = getCacheKey(request);

  let response = await cache.match(cacheKey);
  if (response) {
    return addCacheHeaders(response, 'HIT');
  }

  const originUrl = env.ORIGIN_URL || 'http://localhost:8000';
  const url = new URL(request.url);
  const originRequest = new Request(`${originUrl}${url.pathname}${url.search}`, {
    method: request.method,
    headers: request.headers,
  });

  response = await fetch(originRequest);

  if (response.status === 200) {
    const responseToCache = response.clone();
    ctx.waitUntil(cache.put(cacheKey, responseToCache));
    return addCacheHeaders(response, 'MISS');
  }

  return response;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method !== 'GET' || !isIntelligenceRequest(url)) {
      const originUrl = env.ORIGIN_URL || 'http://localhost:8000';
      return fetch(`${originUrl}${url.pathname}${url.search}`, {
        method: request.method,
        headers: request.headers,
        body: request.body,
      });
    }
    return handleRequest(request, env, ctx);
  },
};
