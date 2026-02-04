# 0007: Dynamic Tiling com MosaicJSON para Deduplicação de Storage

## Status
**Accepted** (2026-02-04)

## Context

### Problema
Arquitetura atual armazena dados de satélite **por AOI**, causando:
- Duplicação de storage quando AOIs se sobrepõem
- Custos crescentes com escala (50MB/AOI/semana × N AOIs)
- Download redundante do mesmo tile Sentinel-2

### Estimativa de Impacto
Para 1000 AOIs com 30% de sobreposição:
- Atual: ~50GB/semana em COGs duplicados
- Custo: ~$15,000/ano em storage + transfer

## Decision

Adotar **Dynamic Tiling com MosaicJSON** usando TiTiler + Planetary Computer como fonte de dados.

### Princípios
1. **Não armazenar rasters derivados por AOI** - Calcular índices on-demand via expressões TiTiler
2. **MosaicJSON para agregação virtual** - Referências às cenas, não dados
3. **CDN cache obrigatório** - Cloudflare para reduzir recomputação
4. **Estatísticas calculadas async** - Worker calcula stats e salva no DB (não em COG)

### Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CAMADA DE VISUALIZAÇÃO                          │
│                                                                     │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌─────────────┐ │
│  │ Frontend │───▶│ Cloudflare│───▶│ TiTiler  │───▶│ MosaicJSON  │ │
│  │ (Leaflet)│    │ CDN       │    │ + Mosaic │    │ (S3)        │ │
│  └──────────┘    └───────────┘    └────┬─────┘    └─────────────┘ │
│                                        │                           │
│                                        ▼                           │
│                               ┌─────────────────┐                  │
│                               │ Planetary       │                  │
│                               │ Computer COGs   │                  │
│                               │ (fonte direta)  │                  │
│                               └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     CAMADA DE ANALYTICS                             │
│                                                                     │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────────────┐ │
│  │Dashboard │───▶│ API       │───▶│ observations_weekly (DB)     │ │
│  │ (Charts) │    │ /stats    │    │ - ndvi_mean, ndvi_p10, etc   │ │
│  └──────────┘    └───────────┘    └──────────────────────────────┘ │
│                                              ▲                      │
│                                              │                      │
│                                   ┌──────────┴─────────┐           │
│                                   │ Worker (async)     │           │
│                                   │ - Calc stats via   │           │
│                                   │   TiTiler/stats    │           │
│                                   │ - Save to DB       │           │
│                                   └────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

#### 1. Criação de AOI (sem mudança no frontend)
```
Frontend: POST /v1/aois {geometry: POLYGON(...)}
    │
    ▼
API: Salva AOI no DB
    │
    ▼
Worker: Job CALCULATE_STATS
    │
    ├─▶ Para cada semana (backfill 8 semanas):
    │     1. Busca MosaicJSON da semana
    │     2. Chama TiTiler /statistics com geometry do AOI
    │     3. Salva stats em observations_weekly
    │
    └─▶ Retorna: AOI pronto para visualização
```

#### 2. Visualização no Mapa
```
Frontend: GET /v1/aois/{id}/tiles/{z}/{x}/{y}.png?index=ndvi&week=5
    │
    ▼
Cloudflare: Cache lookup
    │
    ├─▶ HIT: Retorna tile cacheado (~50ms)
    │
    └─▶ MISS:
          │
          ▼
        TiTiler: /mosaic/tiles/{z}/{x}/{y}
          │      ?url=s3://bucket/mosaics/2026-w05.json
          │      &expression=(B08-B04)/(B08+B04)
          │      &colormap=rdylgn
          │
          ▼
        Planetary Computer: Fetch B04, B08 COGs
          │
          ▼
        TiTiler: Calcula NDVI, aplica colormap
          │
          ▼
        Cloudflare: Cache tile (TTL 7 dias)
          │
          ▼
        Frontend: Exibe tile
```

#### 3. Gráficos e Estatísticas
```
Frontend: GET /v1/aois/{id}/stats?year=2026
    │
    ▼
API: SELECT * FROM observations_weekly WHERE aoi_id = :id
    │
    ▼
Frontend: Renderiza Recharts com dados
```

### Componentes Modificados

#### TiTiler Service
```python
# services/tiler/tiler/main.py
from titiler.core.factory import TilerFactory
from titiler.mosaic.factory import MosaicTilerFactory  # NOVO

app = FastAPI(title="VivaCampo TiTiler")

# COG tiler (manter para compatibilidade)
cog = TilerFactory(router_prefix="/cog")
app.include_router(cog.router, prefix="/cog")

# Mosaic tiler (NOVO)
mosaic = MosaicTilerFactory(router_prefix="/mosaic")
app.include_router(mosaic.router, prefix="/mosaic")
```

#### Worker - Novo Job
```python
# worker/jobs/calculate_stats.py
async def calculate_aoi_stats(payload: dict, db: Session):
    """Calcula estatísticas via TiTiler sem salvar COG."""
    aoi_id = payload["aoi_id"]
    year = payload["year"]
    week = payload["week"]

    aoi = db.query(AOI).get(aoi_id)
    mosaic_url = f"s3://{BUCKET}/mosaics/sentinel-2/{year}/w{week:02d}.json"

    # Chamar TiTiler statistics endpoint
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TILER_URL}/mosaic/statistics",
            params={
                "url": mosaic_url,
                "expression": "(B08-B04)/(B08+B04)",  # NDVI
            },
            json=aoi.geom.__geo_interface__
        )
        stats = response.json()

    # Salvar no DB (não em S3)
    db.execute("""
        INSERT INTO observations_weekly
        (tenant_id, aoi_id, year, week, ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, status)
        VALUES (:tenant_id, :aoi_id, :year, :week, :mean, :p10, :p50, :p90, :std, 'OK')
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version)
        DO UPDATE SET ndvi_mean = :mean, ndvi_p10 = :p10, ...
    """, {
        "tenant_id": aoi.tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "mean": stats["statistics"]["b1"]["mean"],
        "p10": stats["statistics"]["b1"]["percentile_10"],
        "p50": stats["statistics"]["b1"]["percentile_50"],
        "p90": stats["statistics"]["b1"]["percentile_90"],
        "std": stats["statistics"]["b1"]["std"],
    })
```

#### Worker - Gerar MosaicJSON
```python
# worker/jobs/create_mosaic.py
async def create_weekly_mosaic(payload: dict):
    """Cria MosaicJSON para uma semana (job semanal global)."""
    year = payload["year"]
    week = payload["week"]

    # Buscar todas as cenas da semana no Planetary Computer
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )

    start_date, end_date = week_to_date_range(year, week)

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=BRAZIL_BBOX,
        datetime=f"{start_date}/{end_date}",
        query={"eo:cloud_cover": {"lt": 30}}
    )

    items = list(search.items())

    # Criar MosaicJSON
    mosaic_dict = {
        "mosaicjson": "0.0.3",
        "name": f"sentinel-2-{year}-w{week:02d}",
        "minzoom": 8,
        "maxzoom": 14,
        "tiles": {}
    }

    for item in items:
        quadkey = item.properties.get("s2:mgrs_tile")
        mosaic_dict["tiles"][quadkey] = {
            "B02": planetary_computer.sign(item.assets["B02"].href),
            "B03": planetary_computer.sign(item.assets["B03"].href),
            "B04": planetary_computer.sign(item.assets["B04"].href),
            "B08": planetary_computer.sign(item.assets["B08"].href),
            "B11": planetary_computer.sign(item.assets["B11"].href),
            "B12": planetary_computer.sign(item.assets["B12"].href),
            "SCL": planetary_computer.sign(item.assets["SCL"].href),
        }

    # Salvar no S3
    s3_key = f"mosaics/sentinel-2/{year}/w{week:02d}.json"
    s3_client.put_object(
        Bucket=BUCKET,
        Key=s3_key,
        Body=json.dumps(mosaic_dict),
        ContentType="application/json"
    )

    return {"mosaic_url": f"s3://{BUCKET}/{s3_key}", "scenes": len(items)}
```

#### API - Endpoint de Tiles
```python
# services/api/app/presentation/tiles_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/v1/aois", tags=["Tiles"])

EXPRESSIONS = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndwi": "(B03-B08)/(B03+B08)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "evi": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
    "savi": "1.5*(B08-B04)/(B08+B04+0.5)",
}

COLORMAPS = {
    "ndvi": "rdylgn",
    "ndwi": "blues",
    "ndmi": "blues",
    "evi": "rdylgn",
    "savi": "rdylgn",
}

@router.get("/{aoi_id}/tiles/{z}/{x}/{y}.png")
async def get_aoi_tile(
    aoi_id: UUID,
    z: int, x: int, y: int,
    index: str = "ndvi",
    year: int = None,
    week: int = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant)
):
    """Proxy para TiTiler com validação de tenant."""

    # Verificar permissão
    aoi = db.query(AOI).filter_by(id=aoi_id, tenant_id=tenant_id).first()
    if not aoi:
        raise HTTPException(404, "AOI not found")

    # Defaults
    if not year or not week:
        year, week = get_current_iso_week()

    # Construir URL do TiTiler
    mosaic_url = f"s3://{settings.S3_BUCKET}/mosaics/sentinel-2/{year}/w{week:02d}.json"

    tiler_url = (
        f"{settings.TILER_URL}/mosaic/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
        f"?url={mosaic_url}"
        f"&expression={EXPRESSIONS.get(index, EXPRESSIONS['ndvi'])}"
        f"&colormap_name={COLORMAPS.get(index, 'rdylgn')}"
        f"&rescale=-0.2,0.8"
    )

    # Redirect para TiTiler (CDN vai cachear)
    return RedirectResponse(tiler_url, status_code=307)
```

### Storage Final

```
S3 Bucket Structure:
├── mosaics/
│   └── sentinel-2/
│       └── 2026/
│           ├── w01.json    (~50KB)
│           ├── w02.json    (~50KB)
│           └── ...
└── (COGs per-AOI removidos)

Estimativa: ~2.5MB/ano (vs ~2.6TB/ano anterior)
Economia: 99.9%
```

### Migração de Dados Existentes

1. **Manter COGs existentes** temporariamente (30 dias)
2. **Gerar MosaicJSONs** para semanas históricas
3. **Recalcular stats** via novo pipeline
4. **Validar** que dados batem
5. **Remover COGs** antigos

## PoC Results

Teste executado em 2026-02-04:

| Operação | Latência | Observação |
|----------|----------|------------|
| STAC Search | 1,725ms | 1x por sessão |
| 9 tiles NDVI (paralelo) | **483ms** | Sem cache |
| Total cold | 2.2s | Aceitável |
| Com CDN (estimado) | ~50ms | 80-90% requests |

**Veredicto: VIÁVEL**

## Consequences

### Positive
- **99.9% redução de storage** (~2.5MB vs ~2.6TB/ano)
- **64-88% redução de custos** ($1,740-5,400 vs $14,845/ano)
- **Simplicidade** - Worker não baixa/processa COGs
- **Alinhamento** com design do TiTiler
- **Escalabilidade** - CDN escala infinitamente
- **Integração GIS** - XYZ/WMTS funcionam nativamente

### Negative
- **Latência cold** - 2.2s primeira vez (mitigado com loading state)
- **Dependência externa** - Planetary Computer deve estar disponível
- **CDN obrigatório** - Custo adicional (~$240/ano mínimo)

### Neutral
- **Frontend** - Mudança mínima (URL de tiles)
- **Estatísticas** - Mesmo schema no DB
- **Multi-tenant** - Isolamento mantido via API

## Alternatives Considered

### 1. MGRS Tile Data Lake
Armazenar tiles MGRS compartilhados + índices per-AOI.
- **Rejeitado**: Ainda armazena índices, complexidade alta de jobs.

### 2. Content-Addressable Storage
Deduplicação por hash no S3.
- **Rejeitado**: Não reduz downloads, complexo de implementar.

### 3. Manter arquitetura atual
Continuar com COGs per-AOI.
- **Rejeitado**: Custos crescentes insustentáveis em escala.

## References

- [TiTiler Mosaic Documentation](https://developmentseed.org/titiler/advanced/mosaic/)
- [cogeo-mosaic](https://github.com/developmentseed/cogeo-mosaic)
- [MosaicJSON Specification](https://github.com/developmentseed/mosaicjson-spec)
- [Planetary Computer](https://planetarycomputer.microsoft.com/)
- PoC: `scripts/poc/test_latency_simple.py`
