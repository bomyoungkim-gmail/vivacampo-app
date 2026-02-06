/**
 * VivaCampo Tile Cache Worker
 *
 * Cloudflare Worker for caching map tiles served by TiTiler.
 * Part of ADR-0007: Dynamic Tiling with MosaicJSON
 *
 * Features:
 * - Caches successful tile responses for 7 days
 * - Handles redirects from API to TiTiler transparently
 * - Adds performance headers (CF-Cache-Status, X-Cache-TTL)
 * - Respects query parameters in cache key
 *
 * Deploy:
 *   wrangler publish
 *
 * Environment Variables (set in Cloudflare dashboard):
 *   - ORIGIN_URL: API origin URL (e.g., https://api.vivacampo.com.br)
 */

// Cache TTL in seconds (7 days)
const CACHE_TTL = 604800;

// Tile URL pattern: /v1/tiles/aois/{uuid}/{z}/{x}/{y}.png
const TILE_PATTERN = /\/v1\/tiles\/aois\/[0-9a-f-]+\/\d+\/\d+\/\d+\.png/;

// TiTiler internal patterns to cache
const TILER_PATTERNS = [
  /\/mosaic\/tiles\/.*\/\d+\/\d+\/\d+\.png/,
  /\/stac-mosaic\/tiles\/\d+\/\d+\/\d+\.png/,
  /\/cog\/tiles\/.*\/\d+\/\d+\/\d+\.png/,
];

/**
 * Check if request is a tile request that should be cached
 */
function isTileRequest(url) {
  const pathname = url.pathname;

  // Check API tile endpoint
  if (TILE_PATTERN.test(pathname)) {
    return true;
  }

  // Check TiTiler endpoints
  for (const pattern of TILER_PATTERNS) {
    if (pattern.test(pathname)) {
      return true;
    }
  }

  return false;
}

/**
 * Generate cache key from request
 * Includes query parameters for proper cache separation
 */
function getCacheKey(request) {
  const url = new URL(request.url);

  // Sort query params for consistent cache keys
  const params = new URLSearchParams(url.searchParams);
  const sortedParams = new URLSearchParams([...params.entries()].sort());

  // Build canonical URL
  const cacheUrl = `${url.origin}${url.pathname}?${sortedParams.toString()}`;

  return new Request(cacheUrl, {
    method: 'GET',
    headers: request.headers,
  });
}

/**
 * Add cache headers to response
 */
function addCacheHeaders(response, cacheStatus) {
  const headers = new Headers(response.headers);

  // Cache control for downstream caches
  headers.set('Cache-Control', `public, max-age=${CACHE_TTL}, immutable`);

  // Cloudflare cache status
  headers.set('CF-Cache-Status', cacheStatus);

  // Custom headers for debugging
  headers.set('X-Cache-TTL', CACHE_TTL.toString());
  headers.set('X-VivaCampo-Cache', 'tile-worker');

  // Vary header for proper cache separation
  headers.set('Vary', 'Accept-Encoding');

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

/**
 * Handle tile requests with caching
 */
async function handleTileRequest(request, env) {
  const cache = caches.default;
  const cacheKey = getCacheKey(request);

  // Try to get from cache
  let response = await cache.match(cacheKey);

  if (response) {
    // Cache HIT
    return addCacheHeaders(response, 'HIT');
  }

  // Cache MISS - fetch from origin
  const originUrl = env.ORIGIN_URL || 'http://localhost:8000';
  const url = new URL(request.url);

  // Rewrite to origin
  const originRequest = new Request(
    `${originUrl}${url.pathname}${url.search}`,
    {
      method: request.method,
      headers: request.headers,
    }
  );

  response = await fetch(originRequest, {
    // Follow redirects (API redirects to TiTiler)
    redirect: 'follow',
  });

  // Only cache successful responses
  if (response.status === 200) {
    // Clone response for caching
    const responseToCache = response.clone();

    // Cache in background
    const ctx = { waitUntil: (promise) => promise };
    ctx.waitUntil(cache.put(cacheKey, responseToCache));

    return addCacheHeaders(response, 'MISS');
  }

  // Return non-200 responses without caching
  return response;
}

/**
 * Handle non-tile requests (pass through)
 */
async function handleOtherRequest(request, env) {
  const originUrl = env.ORIGIN_URL || 'http://localhost:8000';
  const url = new URL(request.url);

  return fetch(`${originUrl}${url.pathname}${url.search}`, {
    method: request.method,
    headers: request.headers,
    body: request.body,
  });
}

/**
 * Main request handler
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Only process GET requests for tiles
    if (request.method !== 'GET') {
      return handleOtherRequest(request, env);
    }

    // Check if this is a tile request
    if (isTileRequest(url)) {
      return handleTileRequest(request, env);
    }

    // Pass through other requests
    return handleOtherRequest(request, env);
  },
};

/**
 * Scheduled handler for cache warming (optional)
 * Can be triggered via Cloudflare Cron Triggers
 */
export const scheduled = {
  async scheduled(event, env, ctx) {
    // This could be used to pre-warm popular tiles
    // For now, rely on WARM_CACHE job in Worker service
    console.log('Scheduled cache warm trigger - handled by Worker service');
  },
};
