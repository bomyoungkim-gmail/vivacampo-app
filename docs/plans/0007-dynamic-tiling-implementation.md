# Plano de Implementação: Dynamic Tiling + MosaicJSON

**ADR:** 0007-dynamic-tiling-mosaicjson.md
**Data:** 2026-02-04
**Estimativa:** 3-4 sprints (6-8 semanas)

---

## Visão Geral

```
Fase 1: Infraestrutura TiTiler     [Sprint 1] ██████████ DONE
Fase 2: Worker MosaicJSON          [Sprint 1] ██████████ DONE
Fase 3: API Tiles Endpoint         [Sprint 2] ██████████ DONE
Fase 4: Frontend Integration       [Sprint 2] ████████░░ 80%
Fase 5: CDN Setup                  [Sprint 2] ░░░░░░░░░░ TODO
Fase 6: Migration & Cleanup        [Sprint 3] ░░░░░░░░░░ TODO
Fase 7: GIS Integration API        [Sprint 4] ░░░░░░░░░░ TODO
```

### Status Update (2026-02-04)
- **Multi-band support implemented**: `/stac-mosaic/tiles` endpoint working with NDVI, NDRE, NDWI
- **Full pipeline tested**: Auth → API → TiTiler → MosaicJSON → STAC → Planetary Computer → PNG
- **Test results**: NDVI (128KB), NDRE (112KB), NDWI (118KB) tiles generated successfully

---

## Fase 1: Infraestrutura TiTiler

**Objetivo:** Adicionar suporte a MosaicJSON no TiTiler service.

### Tasks

#### TASK-0007-01: Adicionar titiler-mosaic ao TiTiler
**Estimativa:** 2h
**Arquivos:**
- `services/tiler/requirements.txt`
- `services/tiler/tiler/main.py`
- `services/tiler/Dockerfile`

**Mudanças:**
```python
# requirements.txt
titiler.core>=0.18.0
titiler.mosaic>=0.18.0  # NOVO
cogeo-mosaic>=7.0.0     # NOVO
```

```python
# tiler/main.py
from titiler.mosaic.factory import MosaicTilerFactory

# Adicionar router
mosaic = MosaicTilerFactory(
    router_prefix="/mosaic",
    dataset_dependency=MosaicPathParams,
)
app.include_router(mosaic.router, prefix="/mosaic", tags=["Mosaic"])
```

**Acceptance Criteria:**
- [x] `GET /mosaic/tiles/{z}/{x}/{y}.png?url=...` retorna tile
- [x] `POST /mosaic/statistics` retorna stats para geometry
- [x] Health check passa
- [x] `/stac-mosaic/tiles` endpoint para multi-band vegetation indices

**How to test:**
```bash
# Build e run
docker compose build tiler
docker compose up tiler

# Test endpoint
curl "http://localhost:8080/mosaic/tiles/10/300/400.png?url=https://example.com/mosaic.json"
```

---

#### TASK-0007-02: Configurar acesso ao Planetary Computer
**Estimativa:** 1h
**Arquivos:**
- `services/tiler/tiler/main.py`
- `services/tiler/.env.example`

**Mudanças:**
```python
# Configurar planetary-computer signing
import planetary_computer

# Middleware para assinar URLs do PC automaticamente
@app.middleware("http")
async def sign_planetary_computer_urls(request, call_next):
    # Se URL contém planetarycomputer, assinar
    ...
```

**Acceptance Criteria:**
- [x] TiTiler consegue acessar COGs do Planetary Computer
- [x] URLs assinadas automaticamente via `planetary_computer.sign_inplace()`

---

#### TASK-0007-03: Adicionar expressões de índices
**Estimativa:** 1h
**Arquivos:**
- `services/tiler/tiler/expressions.py` (novo)

**Mudanças:**
```python
# expressions.py
VEGETATION_INDICES = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndwi": "(B03-B08)/(B03+B08)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "evi": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
    "savi": "1.5*(B08-B04)/(B08+B04+0.5)",
    "ndre": "(B08-B05)/(B08+B05)",
    "gndvi": "(B08-B03)/(B08+B03)",
    "rvi": "B08/B04",
}

COLORMAPS = {
    "ndvi": "rdylgn",
    "ndwi": "blues",
    # ...
}
```

**Acceptance Criteria:**
- [x] Todos os 14 índices têm expressões definidas
- [x] Colormaps apropriados para cada índice

---

## Fase 2: Worker MosaicJSON

**Objetivo:** Worker gera MosaicJSONs semanais e calcula stats.

### Tasks

#### TASK-0007-04: Criar job CREATE_MOSAIC
**Estimativa:** 4h
**Arquivos:**
- `services/worker/worker/jobs/create_mosaic.py` (novo)
- `services/worker/worker/main.py`

**Mudanças:**
```python
# create_mosaic.py
async def create_weekly_mosaic(payload: dict) -> dict:
    """
    Cria MosaicJSON para uma semana.
    Executado 1x por semana (job global, não per-AOI).
    """
    year = payload["year"]
    week = payload["week"]
    collection = payload.get("collection", "sentinel-2-l2a")

    # 1. Buscar cenas no Planetary Computer
    catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
    start_date, end_date = iso_week_to_dates(year, week)

    search = catalog.search(
        collections=[collection],
        bbox=BRAZIL_BBOX,
        datetime=f"{start_date}/{end_date}",
        query={"eo:cloud_cover": {"lt": 30}}
    )

    items = list(search.items())
    logger.info(f"Found {len(items)} scenes for {year}-W{week:02d}")

    # 2. Construir MosaicJSON
    mosaic = {
        "mosaicjson": "0.0.3",
        "name": f"{collection}-{year}-w{week:02d}",
        "minzoom": 8,
        "maxzoom": 14,
        "center": [-55.0, -15.0, 10],  # Brasil
        "bounds": BRAZIL_BBOX,
        "tiles": {}
    }

    for item in items:
        tile_id = item.properties.get("s2:mgrs_tile", item.id)
        mosaic["tiles"][tile_id] = {
            band: planetary_computer.sign(item.assets[band].href)
            for band in ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"]
            if band in item.assets
        }

    # 3. Salvar no S3
    s3_key = f"mosaics/{collection}/{year}/w{week:02d}.json"
    s3_client.put_object(
        Bucket=BUCKET,
        Key=s3_key,
        Body=json.dumps(mosaic),
        ContentType="application/json"
    )

    return {
        "status": "OK",
        "mosaic_url": f"s3://{BUCKET}/{s3_key}",
        "scenes_count": len(items),
        "tiles_count": len(mosaic["tiles"])
    }
```

**Acceptance Criteria:**
- [x] Job cria MosaicJSON no S3
- [x] MosaicJSON contém STAC item URLs (unsigned, signed at request time)
- [x] Cobertura de Brasil completa (1500+ scenes, 1.5M+ quadkeys)

**How to test:**
```bash
# Enqueue job
python -c "
from worker.main import enqueue_job
enqueue_job('CREATE_MOSAIC', {'year': 2026, 'week': 5})
"

# Verificar S3
aws s3 ls s3://vivacampo-data/mosaics/sentinel-2-l2a/2026/
```

---

#### TASK-0007-05: Criar job CALCULATE_STATS
**Estimativa:** 4h
**Arquivos:**
- `services/worker/worker/jobs/calculate_stats.py` (novo)
- `services/worker/worker/main.py`

**Mudanças:**
```python
# calculate_stats.py
async def calculate_aoi_stats(payload: dict, db: Session) -> dict:
    """
    Calcula estatísticas de índices via TiTiler.
    Substitui o antigo PROCESS_WEEK para stats.
    """
    aoi_id = payload["aoi_id"]
    year = payload["year"]
    week = payload["week"]
    indices = payload.get("indices", ["ndvi", "ndwi", "ndmi", "evi", "savi"])

    # 1. Buscar AOI
    aoi = db.query(AOI).filter_by(id=aoi_id).first()
    if not aoi:
        raise ValueError(f"AOI {aoi_id} not found")

    # 2. Verificar se MosaicJSON existe
    mosaic_url = f"s3://{BUCKET}/mosaics/sentinel-2-l2a/{year}/w{week:02d}.json"
    if not s3_object_exists(mosaic_url):
        # Criar mosaic se não existe
        await create_weekly_mosaic({"year": year, "week": week})

    # 3. Calcular stats para cada índice
    all_stats = {}
    async with httpx.AsyncClient(timeout=60.0) as client:
        for index in indices:
            expression = EXPRESSIONS[index]

            response = await client.post(
                f"{TILER_URL}/mosaic/statistics",
                params={
                    "url": mosaic_url,
                    "expression": expression,
                },
                json=mapping(aoi.geom)  # GeoJSON
            )

            if response.status_code == 200:
                stats = response.json()
                all_stats[index] = {
                    "mean": stats["statistics"]["b1"]["mean"],
                    "min": stats["statistics"]["b1"]["min"],
                    "max": stats["statistics"]["b1"]["max"],
                    "std": stats["statistics"]["b1"]["std"],
                    "p10": stats["statistics"]["b1"]["percentile_10"],
                    "p50": stats["statistics"]["b1"]["percentile_50"],
                    "p90": stats["statistics"]["b1"]["percentile_90"],
                }
            else:
                logger.warning(f"Failed to get stats for {index}: {response.status_code}")
                all_stats[index] = None

    # 4. Salvar no DB
    upsert_observations_weekly(db, aoi, year, week, all_stats)

    return {"status": "OK", "aoi_id": str(aoi_id), "indices": list(all_stats.keys())}
```

**Acceptance Criteria:**
- [ ] Job calcula stats via TiTiler
- [ ] Stats salvos em `observations_weekly`
- [ ] Funciona para todos os 14 índices

---

#### TASK-0007-06: Modificar BACKFILL para novo pipeline
**Estimativa:** 2h
**Arquivos:**
- `services/worker/worker/jobs/backfill.py`

**Mudanças:**
```python
# backfill.py - Modificar para usar novo pipeline
async def backfill_aoi(payload: dict, db: Session) -> dict:
    aoi_id = payload["aoi_id"]
    weeks = payload.get("weeks", 8)

    # 1. Calcular semanas para backfill
    today = date.today()
    target_weeks = []
    for i in range(weeks):
        d = today - timedelta(weeks=i)
        year, week, _ = d.isocalendar()
        target_weeks.append((year, week))

    # 2. Garantir MosaicJSONs existem
    for year, week in target_weeks:
        mosaic_url = f"s3://{BUCKET}/mosaics/sentinel-2-l2a/{year}/w{week:02d}.json"
        if not s3_object_exists(mosaic_url):
            enqueue_job("CREATE_MOSAIC", {"year": year, "week": week})

    # 3. Enqueue stats jobs
    for year, week in target_weeks:
        enqueue_job("CALCULATE_STATS", {
            "aoi_id": str(aoi_id),
            "year": year,
            "week": week,
        })

    # 4. Enqueue weather (mantém igual)
    enqueue_job("PROCESS_WEATHER", {"aoi_id": str(aoi_id), ...})

    return {"status": "OK", "weeks_queued": len(target_weeks)}
```

**Acceptance Criteria:**
- [ ] BACKFILL usa CALCULATE_STATS em vez de PROCESS_WEEK
- [ ] MosaicJSONs criados automaticamente se não existem

---

#### TASK-0007-07: Job scheduler semanal para MosaicJSON
**Estimativa:** 2h
**Arquivos:**
- `services/worker/worker/scheduler.py` (novo ou existente)

**Mudanças:**
```python
# Cron job: toda segunda-feira às 06:00 UTC
# Cria MosaicJSON da semana anterior

@scheduler.scheduled_job("cron", day_of_week="mon", hour=6)
async def create_weekly_mosaics():
    today = date.today()
    year, week, _ = (today - timedelta(days=7)).isocalendar()

    # Sentinel-2
    enqueue_job("CREATE_MOSAIC", {
        "year": year,
        "week": week,
        "collection": "sentinel-2-l2a"
    })

    # Sentinel-1 (radar)
    enqueue_job("CREATE_MOSAIC", {
        "year": year,
        "week": week,
        "collection": "sentinel-1-rtc"
    })

    logger.info(f"Scheduled mosaic creation for {year}-W{week:02d}")
```

**Acceptance Criteria:**
- [ ] Scheduler executa toda segunda
- [ ] MosaicJSON de S2 e S1 criados automaticamente

---

## Fase 3: API Tiles Endpoint

**Objetivo:** API proxy para TiTiler com autenticação.

### Tasks

#### TASK-0007-08: Criar tiles_router.py
**Estimativa:** 3h
**Arquivos:**
- `services/api/app/presentation/tiles_router.py` (novo)
- `services/api/app/main.py`

**Mudanças:**
```python
# tiles_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from uuid import UUID

router = APIRouter(prefix="/v1/tiles", tags=["Tiles"])

@router.get("/aois/{aoi_id}/{z}/{x}/{y}.png")
async def get_aoi_tile(
    aoi_id: UUID,
    z: int,
    x: int,
    y: int,
    index: str = Query("ndvi", regex="^(ndvi|ndwi|ndmi|evi|savi|ndre|gndvi)$"),
    year: int = Query(None),
    week: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Serve tile PNG para AOI específico.
    Proxy autenticado para TiTiler com CDN caching.
    """
    # 1. Verificar permissão
    aoi = db.query(AOI).filter_by(
        id=aoi_id,
        tenant_id=current_user.tenant_id
    ).first()

    if not aoi:
        raise HTTPException(404, "AOI not found")

    # 2. Defaults para ano/semana atual
    if not year or not week:
        today = date.today()
        year, week, _ = today.isocalendar()

    # 3. Construir URL do TiTiler
    mosaic_url = f"s3://{settings.S3_BUCKET}/mosaics/sentinel-2-l2a/{year}/w{week:02d}.json"

    expression = EXPRESSIONS[index]
    colormap = COLORMAPS[index]

    tiler_url = (
        f"{settings.TILER_INTERNAL_URL}/mosaic/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
        f"?url={quote(mosaic_url)}"
        f"&expression={quote(expression)}"
        f"&colormap_name={colormap}"
        f"&rescale=-0.2,0.8"
    )

    # 4. Redirect (CDN vai cachear)
    response = RedirectResponse(tiler_url, status_code=307)
    response.headers["Cache-Control"] = "public, max-age=604800"  # 7 dias
    return response


@router.get("/aois/{aoi_id}/tilejson.json")
async def get_aoi_tilejson(
    aoi_id: UUID,
    index: str = "ndvi",
    year: int = None,
    week: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna TileJSON para integração com GIS tools.
    """
    aoi = db.query(AOI).filter_by(id=aoi_id, tenant_id=current_user.tenant_id).first()
    if not aoi:
        raise HTTPException(404, "AOI not found")

    if not year or not week:
        today = date.today()
        year, week, _ = today.isocalendar()

    bounds = shape(aoi.geom).bounds

    return {
        "tilejson": "3.0.0",
        "name": f"{aoi.name} - {index.upper()}",
        "tiles": [
            f"{settings.API_BASE_URL}/v1/tiles/aois/{aoi_id}/{{z}}/{{x}}/{{y}}.png?index={index}&year={year}&week={week}"
        ],
        "minzoom": 8,
        "maxzoom": 16,
        "bounds": list(bounds),
        "center": [
            (bounds[0] + bounds[2]) / 2,
            (bounds[1] + bounds[3]) / 2,
            12
        ]
    }
```

**Acceptance Criteria:**
- [x] Endpoint retorna tiles PNG
- [x] Autenticação por tenant funciona
- [x] TileJSON retorna metadata correta
- [x] Cache headers configurados (7 days)

**How to test:**
```bash
# Com token de autenticação
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/tiles/aois/{aoi_id}/13/2847/4523.png?index=ndvi"
```

---

#### TASK-0007-09: Endpoint de export COG
**Estimativa:** 2h
**Arquivos:**
- `services/api/app/presentation/tiles_router.py`

**Mudanças:**
```python
@router.post("/aois/{aoi_id}/export")
async def export_aoi_cog(
    aoi_id: UUID,
    index: str = "ndvi",
    year: int = None,
    week: int = None,
    format: str = "cog",  # cog, geotiff, png
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
):
    """
    Gera COG on-demand para download.
    Para integração com GIS que precisam arquivo local.
    """
    aoi = db.query(AOI).filter_by(id=aoi_id, tenant_id=current_user.tenant_id).first()
    if not aoi:
        raise HTTPException(404, "AOI not found")

    # Gerar COG via TiTiler e salvar em S3
    export_key = f"exports/{current_user.tenant_id}/{aoi_id}/{index}-{year}-w{week}.tif"

    # Enqueue background job
    background_tasks.add_task(
        generate_cog_export,
        aoi=aoi,
        index=index,
        year=year,
        week=week,
        s3_key=export_key
    )

    # Retornar URL presigned (válido por 24h)
    presigned_url = generate_presigned_url(export_key, expiration=86400)

    return {
        "status": "processing",
        "download_url": presigned_url,
        "expires_in": 86400,
        "format": format
    }
```

**Acceptance Criteria:**
- [x] Endpoint gera COG on-demand
- [x] Presigned URL válido por 24h
- [ ] Suporta formatos: COG, GeoTIFF, PNG (only COG implemented)

---

## Fase 4: Frontend Integration

**Objetivo:** Atualizar frontend para usar novo endpoint de tiles.

### Tasks

#### TASK-0007-10: Atualizar MapLeaflet.tsx
**Estimativa:** 2h
**Arquivos:**
- `services/app-ui/src/components/MapLeaflet.tsx`

**Mudanças:**
```typescript
// Antes
const getTileUrl = (aoi: AOI, index: string) => {
  return `${TILER_URL}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(aoi.assets[index].tile_url)}`;
};

// Depois
const getTileUrl = (aoi: AOI, index: string, year?: number, week?: number) => {
  const params = new URLSearchParams({
    index,
    ...(year && { year: year.toString() }),
    ...(week && { week: week.toString() }),
  });
  return `${API_URL}/v1/tiles/aois/${aoi.id}/{z}/{x}/{y}.png?${params}`;
};
```

**Acceptance Criteria:**
- [ ] Tiles carregam do novo endpoint
- [ ] Seletor de índice funciona
- [ ] Seletor de semana funciona

---

#### TASK-0007-11: Adicionar loading skeleton
**Estimativa:** 1h
**Arquivos:**
- `services/app-ui/src/components/MapLeaflet.tsx`
- `services/app-ui/src/components/TileSkeleton.tsx` (novo)

**Mudanças:**
```typescript
// TileSkeleton.tsx
export const TileSkeleton = () => (
  <div className="absolute inset-0 bg-muted animate-pulse" />
);

// MapLeaflet.tsx
<TileLayer
  url={getTileUrl(aoi, selectedIndex)}
  eventHandlers={{
    loading: () => setIsLoading(true),
    load: () => setIsLoading(false),
  }}
/>
{isLoading && <TileSkeleton />}
```

**Acceptance Criteria:**
- [ ] Skeleton aparece durante loading
- [ ] Transição suave ao carregar

---

#### TASK-0007-12: Prefetch de tiles adjacentes
**Estimativa:** 2h
**Arquivos:**
- `services/app-ui/src/hooks/useTilePrefetch.ts` (novo)
- `services/app-ui/src/components/MapLeaflet.tsx`

**Mudanças:**
```typescript
// useTilePrefetch.ts
export const useTilePrefetch = (aoiId: string, index: string) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    const prefetchVisibleTiles = () => {
      const bounds = map.getBounds();
      const zoom = map.getZoom();

      // Calcular tiles visíveis + margem
      const tiles = getTilesInBounds(bounds, zoom, margin: 1);

      // Prefetch em background
      tiles.forEach(({ z, x, y }) => {
        const img = new Image();
        img.src = `${API_URL}/v1/tiles/aois/${aoiId}/${z}/${x}/${y}.png?index=${index}`;
      });
    };

    map.on('moveend', prefetchVisibleTiles);
    return () => map.off('moveend', prefetchVisibleTiles);
  }, [map, aoiId, index]);
};
```

**Acceptance Criteria:**
- [ ] Tiles adjacentes pré-carregados
- [ ] Navegação mais fluida

---

## Fase 5: CDN Setup

**Objetivo:** Configurar Cloudflare para caching de tiles.

### Tasks

#### TASK-0007-13: Configurar Cloudflare
**Estimativa:** 2h
**Arquivos:**
- `infra/cloudflare/workers/tile-cache.js` (novo)
- `docs/runbooks/cloudflare-setup.md` (novo)

**Mudanças:**
```javascript
// tile-cache.js - Cloudflare Worker
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // Apenas cachear rotas de tiles
  if (!url.pathname.match(/\/v1\/tiles\/.*\/\d+\/\d+\/\d+\.png/)) {
    return fetch(request);
  }

  // Cache key inclui query params
  const cacheKey = new Request(url.toString(), request);
  const cache = caches.default;

  // Verificar cache
  let response = await cache.match(cacheKey);
  if (response) {
    return response;
  }

  // Fetch do origin
  response = await fetch(request);

  // Cachear se sucesso
  if (response.status === 200) {
    response = new Response(response.body, response);
    response.headers.set('Cache-Control', 'public, max-age=604800'); // 7 dias
    event.waitUntil(cache.put(cacheKey, response.clone()));
  }

  return response;
}
```

**Acceptance Criteria:**
- [ ] Cloudflare configurado
- [ ] Cache hit rate > 80% após warmup
- [ ] Latência < 100ms para cache hits

---

#### TASK-0007-14: Cache warming job
**Estimativa:** 2h
**Arquivos:**
- `services/worker/worker/jobs/warm_cache.py` (novo)

**Mudanças:**
```python
# warm_cache.py
async def warm_aoi_cache(payload: dict):
    """
    Pré-carrega tiles para AOI recém-criado.
    Executado após BACKFILL completar.
    """
    aoi_id = payload["aoi_id"]
    index = payload.get("index", "ndvi")

    aoi = db.query(AOI).get(aoi_id)
    bounds = shape(aoi.geom).bounds

    # Zoom levels típicos para agricultura
    for z in range(10, 15):
        tiles = list(mercantile.tiles(*bounds, zooms=z))

        async with httpx.AsyncClient() as client:
            tasks = [
                client.get(
                    f"{CDN_URL}/v1/tiles/aois/{aoi_id}/{z}/{t.x}/{t.y}.png",
                    params={"index": index}
                )
                for t in tiles[:100]  # Limitar para não sobrecarregar
            ]
            await asyncio.gather(*tasks)

    logger.info(f"Warmed cache for AOI {aoi_id}")
```

**Acceptance Criteria:**
- [ ] Cache warming executa após backfill
- [ ] Primeiro acesso do usuário é rápido

---

## Fase 6: Migration & Cleanup

**Objetivo:** Migrar dados existentes e remover código antigo.

### Tasks

#### TASK-0007-15: Script de migração de stats
**Estimativa:** 4h
**Arquivos:**
- `scripts/migrate_to_dynamic_tiling.py` (novo)

**Mudanças:**
```python
# migrate_to_dynamic_tiling.py
"""
Migração:
1. Gerar MosaicJSONs para semanas históricas
2. Recalcular stats via novo pipeline
3. Validar que stats batem com existentes
4. Marcar AOIs como migrados
"""

async def migrate_aoi(aoi_id: UUID):
    aoi = db.query(AOI).get(aoi_id)

    # Buscar semanas com dados existentes
    existing_weeks = db.query(DerivedAssets.year, DerivedAssets.week).filter_by(
        aoi_id=aoi_id
    ).distinct().all()

    for year, week in existing_weeks:
        # Garantir mosaic existe
        await ensure_mosaic_exists(year, week)

        # Calcular stats via novo pipeline
        new_stats = await calculate_stats_via_tiler(aoi, year, week)

        # Comparar com stats antigos
        old_stats = db.query(DerivedAssets).filter_by(
            aoi_id=aoi_id, year=year, week=week
        ).first()

        if abs(new_stats["ndvi_mean"] - old_stats.ndvi_mean) > 0.01:
            logger.warning(f"Stats mismatch for {aoi_id} {year}-W{week}")

    # Marcar como migrado
    aoi.migration_status = "DYNAMIC_TILING"
    db.commit()
```

**Acceptance Criteria:**
- [ ] Script migra AOIs existentes
- [ ] Validação de stats passa
- [ ] Rollback possível

---

#### TASK-0007-16: Remover código de COG storage
**Estimativa:** 2h
**Arquivos:**
- `services/worker/worker/jobs/process_week.py` (deprecate)
- `services/api/app/presentation/aois_router.py`

**Mudanças:**
- Marcar `PROCESS_WEEK` como deprecated
- Remover lógica de upload de COG
- Manter para rollback por 30 dias

**Acceptance Criteria:**
- [ ] Código antigo marcado deprecated
- [ ] Nenhum novo COG criado
- [ ] Feature flag para rollback

---

#### TASK-0007-17: Cleanup de COGs antigos
**Estimativa:** 1h
**Arquivos:**
- `scripts/cleanup_old_cogs.py` (novo)

**Mudanças:**
```python
# Executar após 30 dias de migração estável
async def cleanup_old_cogs():
    """Remove COGs per-AOI antigos do S3."""

    # Listar objetos com padrão antigo
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix='tenant='):
        for obj in page.get('Contents', []):
            if '/indices/' not in obj['Key']:  # Preservar se for novo formato
                s3_client.delete_object(Bucket=BUCKET, Key=obj['Key'])
                logger.info(f"Deleted: {obj['Key']}")
```

**Acceptance Criteria:**
- [ ] COGs antigos removidos
- [ ] Storage liberado
- [ ] Apenas após validação completa

---

## Fase 7: GIS Integration API

**Objetivo:** Endpoints para integração com QGIS/ArcGIS.

### Tasks

#### TASK-0007-18: WMTS Capabilities endpoint
**Estimativa:** 2h
**Arquivos:**
- `services/api/app/presentation/tiles_router.py`

**Mudanças:**
```python
@router.get("/wmts")
async def wmts_capabilities(
    service: str = "WMTS",
    request: str = "GetCapabilities",
):
    """
    WMTS GetCapabilities para integração com GIS enterprise.
    """
    # Gerar XML de capabilities
    capabilities = generate_wmts_capabilities(
        layers=["ndvi", "ndwi", "ndmi", "evi", "savi"],
        base_url=settings.API_BASE_URL
    )
    return Response(content=capabilities, media_type="application/xml")
```

**Acceptance Criteria:**
- [ ] WMTS capabilities válido
- [ ] QGIS consegue adicionar layer
- [ ] ArcGIS consegue adicionar layer

---

#### TASK-0007-19: Documentação de integração GIS
**Estimativa:** 2h
**Arquivos:**
- `docs/features/gis-integration.md` (novo)

**Conteúdo:**
- Setup QGIS com XYZ tiles
- Setup ArcGIS com WMTS
- Autenticação via API key
- Exemplos de URLs

**Acceptance Criteria:**
- [ ] Documentação completa
- [ ] Testado com QGIS 3.x
- [ ] Testado com ArcGIS Pro

---

## Checklist de Validação Final

### Funcional
- [ ] AOI creation funciona (frontend)
- [ ] Mapa exibe tiles corretamente
- [ ] Troca de índice funciona
- [ ] Troca de semana funciona
- [ ] Charts exibem estatísticas corretas
- [ ] Export COG funciona
- [ ] Integração QGIS funciona

### Performance
- [ ] Latência cold < 3s
- [ ] Latência warm < 100ms (CDN)
- [ ] Cache hit rate > 80%

### Segurança
- [ ] Tenant isolation mantido
- [ ] Autenticação obrigatória
- [ ] Rate limiting configurado

### Observabilidade
- [ ] Logs estruturados
- [ ] Métricas de latência
- [ ] Alertas configurados

---

## Rollback Plan

### Trigger
- Latência p95 > 5s por mais de 30min
- Error rate > 5%
- Planetary Computer indisponível por > 1h

### Passos
1. Feature flag: `USE_DYNAMIC_TILING=false`
2. Worker volta a usar PROCESS_WEEK
3. API volta a servir COGs do S3
4. Notificar equipe

### Tempo estimado de rollback
- Automático via feature flag: < 5min
- Manual: < 30min

---

## Timeline

| Sprint | Fase | Tasks | Estimativa |
|--------|------|-------|------------|
| 1 | 1, 2 | TASK-0007-01 a 07 | 16h |
| 2 | 3, 4, 5 | TASK-0007-08 a 14 | 16h |
| 3 | 6 | TASK-0007-15 a 17 | 7h |
| 4 | 7 | TASK-0007-18 a 19 | 4h |

**Total estimado:** 43h (~5-6 dias de trabalho)

---

## Dependências Externas

| Dependência | Criticidade | Fallback |
|-------------|-------------|----------|
| Planetary Computer | Alta | Copernicus Hub (mais lento) |
| Cloudflare | Média | AWS CloudFront |
| TiTiler | Alta | Self-hosted com backup |

---

## Métricas de Sucesso

| Métrica | Target | Atual |
|---------|--------|-------|
| Storage cost | -90% | baseline |
| Latência p50 | < 500ms | TBD |
| Latência p95 | < 2s | TBD |
| Cache hit rate | > 80% | TBD |
| Error rate | < 1% | TBD |
