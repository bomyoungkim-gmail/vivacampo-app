# VivaCampo MVP - Testes E2E

## Executar Testes

### Pré-requisitos
```bash
# Instalar pytest
pip install pytest requests

# Iniciar todos os serviços
cd c:\projects\vivacampo-app
docker compose up -d

# Aguardar serviços iniciarem
docker compose ps

# Aplicar migrations
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/001_initial_schema.sql
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql
```

### Executar Testes E2E
```bash
cd c:\projects\vivacampo-app
python tests/test_e2e.py
```

### Testes Incluídos
1. ✅ Health check
2. ✅ OIDC login
3. ✅ Workspace switch
4. ✅ Create farm
5. ✅ List farms
6. ✅ List signals
7. ✅ Create AI assistant thread
8. ✅ List AI threads
9. ✅ Metrics endpoint
10. ✅ OpenAPI docs

## Testar Frontend

```bash
# Instalar dependências
cd services/app-ui
npm install

# Executar em dev mode
npm run dev

# Acessar
# http://localhost:3002/app/
```

## Testar TiTiler

```bash
# Verificar health
curl http://localhost:8080/health

# Testar tile endpoint (requer COG no S3)
curl "http://localhost:8080/cog/tiles/14/8192/8192?url=s3://vivacampo-derived-local/tenant=xxx/aoi=xxx/year=2024/week=1/pipeline=v1/ndvi.tif"
```

## Status Final

✅ **Todas as 8 Fases Completas!**

1. ✅ Infraestrutura & Database
2. ✅ Backend Core (API)
3. ✅ EO Pipeline (Worker)
4. ✅ Signals Engine
5. ✅ AI Assistant (Multi-Provider)
6. ✅ Frontend (App UI)
7. ✅ TiTiler Service
8. ✅ E2E Tests
