# Análise de Viabilidade: Dynamic Tiling + MosaicJSON

## Preocupações do Stakeholder

1. **Integração GIS** - Vai funcionar com QGIS/ArcGIS do cliente?
2. **Performance** - Lag vai deixar usuário insatisfeito?
3. **Custos AWS** - Vai ficar mais caro que armazenar COGs?

---

## 1. Integração com GIS do Cliente

### Como QGIS/ArcGIS consomem tiles

| Ferramenta | Protocolo | Requisitos |
|------------|-----------|------------|
| QGIS | XYZ Tiles, WMS, WMTS, COG direto | URL pública ou com token |
| ArcGIS Pro | XYZ Tiles, WMS, WMTS | URL pública ou com token |
| ArcGIS Online | XYZ Tiles, WMS | URL HTTPS pública |
| Google Earth Engine | XYZ Tiles | URL pública |

### O que TiTiler/Mosaic oferece

```
Endpoints disponíveis:
├── /mosaic/tiles/{z}/{x}/{y}.png      ← XYZ (funciona em todos GIS)
├── /mosaic/tiles/{z}/{x}/{y}.tif      ← GeoTIFF tile (análise)
├── /mosaic/WMTSCapabilities.xml       ← WMTS (padrão OGC)
├── /mosaic/tilejson.json              ← TileJSON metadata
└── /cog/tiles/{z}/{x}/{y}             ← COG direto (fallback)
```

### Cenários de Integração

#### Cenário A: Cliente quer visualizar no QGIS
```
QGIS → Add XYZ Layer → URL:
https://api.vivacampo.com/v1/tiles/aoi/{aoi_id}/{z}/{x}/{y}.png?token={api_key}&index=ndvi
```
**Funciona?** ✅ Sim, XYZ é universal

#### Cenário B: Cliente quer baixar COG para análise local
```
API Endpoint:
GET /v1/aois/{aoi_id}/export?format=cog&index=ndvi&year=2026&week=5

Retorna:
{
  "download_url": "https://presigned-s3-url/aoi-123-ndvi-2026-w05.tif",
  "expires_in": 3600
}
```
**Funciona?** ✅ Sim, geramos COG on-demand (cache 24h)

#### Cenário C: Cliente quer WMS para sistema legado
```
WMTS Capabilities:
https://api.vivacampo.com/v1/tiles/wmts?service=WMTS&request=GetCapabilities
```
**Funciona?** ✅ Sim, TiTiler suporta WMTS nativo

### Conclusão GIS Integration
| Protocolo | Suportado | Notas |
|-----------|-----------|-------|
| XYZ Tiles | ✅ | Universal, funciona em tudo |
| WMTS | ✅ | Padrão OGC, empresas grandes |
| WMS | ✅ | Legacy, mais lento |
| COG Download | ✅ | Gerado on-demand, cacheado |
| GeoJSON Stats | ✅ | Para dashboards externos |

**Resposta: SIM, integração GIS funciona perfeitamente.**

---

## 2. Performance e Latência

### Breakdown de Latência (sem cache)

```
Request: GET /tiles/aoi/123/15/10234/12345.png?index=ndvi

Timeline:
├── [50ms]   API Gateway + Auth
├── [100ms]  TiTiler parse request
├── [500ms]  Fetch MosaicJSON from S3
├── [800ms]  Planetary Computer: fetch B04 tile
├── [800ms]  Planetary Computer: fetch B08 tile
├── [200ms]  Calculate NDVI expression
├── [100ms]  Render PNG + colormap
└── [50ms]   Response
─────────────────────────────────────
Total: ~2.5-3 segundos (cold)
```

### Com CDN Cache (Cloudflare)

```
Cache HIT (tile já solicitado):
├── [20ms]   Cloudflare edge
└── [30ms]   Response
─────────────────────────────────────
Total: ~50ms ✅

Cache MISS (primeiro request):
├── [20ms]   Cloudflare edge
├── [2500ms] Origin (TiTiler + PC)
├── [10ms]   Cache write
└── [30ms]   Response
─────────────────────────────────────
Total: ~2.6 segundos (primeira vez)
Próximos requests: ~50ms
```

### Comparação com Alternativa A (COG pré-armazenado)

| Cenário | MGRS Data Lake | Dynamic + MosaicJSON |
|---------|----------------|----------------------|
| Cache HIT | ~100ms | ~50ms (CDN edge) |
| Cache MISS | ~200ms (S3 direto) | ~2.5s (PC + calc) |
| Pan/Zoom rápido | ✅ Consistente | ⚠️ Depende do cache |

### Mitigações para Latência

#### 1. Cache Warming (pré-aquecer cache)
```python
# Worker job: pré-gerar tiles mais usados
async def warm_cache(aoi_id: UUID, year: int, week: int):
    """Pré-solicita tiles nos zoom levels mais usados."""
    aoi = db.query(AOI).get(aoi_id)
    bbox = aoi.geom.bounds

    # Zoom levels típicos para agricultura: 12-16
    for z in range(12, 17):
        tiles = mercantile.tiles(*bbox, zooms=z)
        for tile in tiles:
            # Request para popular cache
            await http_client.get(
                f"{CDN_URL}/tiles/aoi/{aoi_id}/{z}/{tile.x}/{tile.y}.png"
            )
```

#### 2. Prefetch no Frontend
```typescript
// Quando usuário seleciona AOI, pré-carregar tiles visíveis
useEffect(() => {
  if (selectedAoi) {
    const bounds = selectedAoi.geometry.bounds;
    const currentZoom = map.getZoom();

    // Prefetch tiles adjacentes
    prefetchTilesInBounds(bounds, currentZoom, selectedAoi.id);
  }
}, [selectedAoi]);
```

#### 3. Skeleton Loading + Progressive Enhancement
```typescript
// Mostrar placeholder enquanto carrega
<MapLayer
  url={tileUrl}
  loading={<SkeletonTile />}
  errorFallback={<CachedTile />}
/>
```

#### 4. Stale-While-Revalidate
```
Cache-Control: public, max-age=86400, stale-while-revalidate=604800
```
- Serve cache antigo imediatamente
- Atualiza em background

### Experiência do Usuário Real

| Ação | Sem mitigação | Com mitigações |
|------|---------------|----------------|
| Abrir mapa (primeira vez) | 3s loading | 3s, mas com skeleton |
| Pan/Zoom (cache quente) | 50ms | 50ms |
| Trocar semana | 3s | 500ms (prefetch) |
| Trocar índice | 3s | 1s (partial cache) |

### Conclusão Performance
**Com CDN + cache warming + UX apropriada:**
- **90% dos requests**: <100ms ✅
- **10% dos requests**: 2-3s (aceitável com loading state)

**Resposta: Lag controlável com estratégia de cache.**

---

## 3. Análise de Custos AWS

### Cenário: 1000 AOIs, 52 semanas, 14 índices

#### Alternativa A: MGRS Data Lake (armazenar COGs)

```
STORAGE (S3):
├── Raw tiles MGRS: 500 tiles × 500MB × 52 semanas = 13 TB/ano
├── Índices per-AOI: 1000 AOIs × 50MB × 52 semanas = 2.6 TB/ano
└── Total: ~15.6 TB/ano

S3 Standard: $0.023/GB/mês
Custo storage: 15,600 GB × $0.023 × 12 = $4,305/ano

COMPUTE (Worker):
├── Download: 500 tiles × 52 semanas × $0.10 = $2,600/ano
├── Processing: 1000 AOIs × 52 semanas × $0.05 = $2,600/ano
└── Total compute: ~$5,200/ano

TRANSFER (S3 → TiTiler):
├── Requests: 1000 AOIs × 1000 tiles/mês × $0.0004 = $400/mês
├── Egress: ~500GB/mês × $0.09 = $45/mês
└── Total: ~$5,340/ano

────────────────────────────────────
TOTAL ALTERNATIVA A: ~$14,845/ano
────────────────────────────────────
```

#### Alternativa B: Dynamic + MosaicJSON

```
STORAGE (S3):
├── MosaicJSON: 52 semanas × 10KB = 520KB (~$0)
├── Stats cache: 1000 AOIs × 52 × 1KB = 52MB (~$0)
└── Total: ~negligível

COMPUTE (TiTiler):
├── EC2 t3.large (2 instâncias): $0.0832/hr × 24 × 365 × 2 = $1,458/ano
├── OU Lambda (se serverless): ~$3,000/ano (depende do uso)
└── Total compute: ~$1,500-3,000/ano

CDN (Cloudflare):
├── Pro plan: $20/mês = $240/ano
├── OU Enterprise: ~$200/mês = $2,400/ano
└── Total CDN: ~$240-2,400/ano

PLANETARY COMPUTER:
├── API calls: GRÁTIS (Microsoft subsidia)
├── Egress: GRÁTIS (servido do Azure blob)
└── Total: $0

TRANSFER (CDN → Users):
├── Cloudflare: GRÁTIS (unlimited bandwidth)
└── Total: $0

────────────────────────────────────
TOTAL ALTERNATIVA B: ~$1,740-5,400/ano
────────────────────────────────────
```

### Comparação de Custos

| Item | Alt. A (MGRS) | Alt. B (Dynamic) | Economia |
|------|---------------|------------------|----------|
| Storage S3 | $4,305 | ~$0 | 100% |
| Compute | $5,200 | $1,500-3,000 | 42-71% |
| Transfer | $5,340 | $240-2,400 | 55-95% |
| **TOTAL** | **$14,845** | **$1,740-5,400** | **64-88%** |

### Cenário de Escala (10,000 AOIs)

| Métrica | Alt. A | Alt. B |
|---------|--------|--------|
| Storage | ~$43,000/ano | ~$0 |
| Compute | ~$52,000/ano | ~$10,000/ano |
| Transfer | ~$53,000/ano | ~$5,000/ano |
| **TOTAL** | **~$148,000/ano** | **~$15,000/ano** |

**Economia em escala: ~90%**

### Riscos de Custo na Alternativa B

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Planetary Computer muda pricing | Baixa | Alto | Fallback para Copernicus Hub |
| CDN cache miss alto | Média | Médio | Cache warming agressivo |
| Compute spike (muitos usuários) | Média | Médio | Auto-scaling + rate limiting |
| Cloudflare muda plano | Baixa | Baixo | Alternativas: Fastly, AWS CloudFront |

### Conclusão Custos
**Alternativa B é significativamente mais barata:**
- **Economia imediata**: 64-88%
- **Economia em escala**: ~90%
- **Risco principal**: Dependência do Planetary Computer (mitigável)

**Resposta: Custos AWS serão MENORES, não maiores.**

---

## Resumo Executivo

| Preocupação | Resposta | Confiança |
|-------------|----------|-----------|
| **Integração GIS** | ✅ Funciona (XYZ, WMTS, COG download) | Alta |
| **Performance/Lag** | ✅ Controlável (CDN + cache warming) | Média-Alta |
| **Custos AWS** | ✅ 64-88% mais barato | Alta |

### Recomendação

**Prosseguir com Alternativa B (Dynamic + MosaicJSON)** com:

1. **CDN obrigatório** (Cloudflare Pro mínimo)
2. **Cache warming** para AOIs ativos
3. **Fallback strategy** para Planetary Computer downtime
4. **Export COG endpoint** para clientes que precisam arquivo local

### Próximos Passos

1. [ ] PoC: TiTiler + cogeo-mosaic (1 dia)
2. [ ] PoC: Latência real com Planetary Computer (1 dia)
3. [ ] PoC: Integração QGIS (meio dia)
4. [ ] Decisão final baseada em PoC
5. [ ] Implementação (2-3 sprints)
