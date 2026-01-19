# VivaCampo - Guia de Setup Completo

## Pré-requisitos

- Docker Desktop instalado e rodando
- Node.js 20+ instalado
- Python 3.11+ instalado
- Git

---

## 1. Setup do Projeto

### Clonar/Navegar para o projeto
```bash
cd c:\projects\vivacampo-app
```

---

## 2. Instalar Dependências do Frontend

### App UI
```bash
cd services/app-ui
npm install
cd ../..
```

### Admin UI
```bash
cd services/admin-ui
npm install
cd ../..
```

**Isso vai resolver todos os erros do TypeScript que você está vendo!**

---

## 3. Iniciar Infraestrutura (Docker)

### Opção A: Todos os serviços
```bash
docker compose up -d
```

### Opção B: Apenas infraestrutura (recomendado para desenvolvimento)
```bash
# Apenas DB, Redis, LocalStack
docker compose up -d db redis localstack

# Aguardar serviços ficarem prontos (30s)
timeout /t 30

# Aplicar migrations
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/001_initial_schema.sql
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql
```

---

## 4. Rodar Serviços Localmente (Desenvolvimento)

### API (FastAPI)
```bash
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Worker (Python)
```bash
cd services/worker
pip install -r requirements.txt
python -m worker.main
```

### App UI (Next.js)
```bash
cd services/app-ui
npm run dev
# Acesse: http://localhost:3002
```

### Admin UI (Next.js)
```bash
cd services/admin-ui
npm run dev
# Acesse: http://localhost:3001/admin
```

---

## 5. Verificar Health

### API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```

### Database
```bash
docker compose exec db psql -U vivacampo -d vivacampo -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
# Deve retornar 25+ tabelas
```

### Redis
```bash
docker compose exec redis redis-cli ping
# Deve retornar: PONG
```

---

## 6. Executar Testes

### Testes de Integração (Backend)
```bash
# Com serviços rodando
pytest tests/test_integration_complete.py -v --asyncio-mode=auto
```

### Testes E2E (Frontend)
```bash
# Instalar Playwright
npx playwright install

# Rodar testes
npx playwright test

# Ver relatório
npx playwright show-report
```

### Validação de Infraestrutura
```bash
cd tests
bash test_validation.sh
```

---

## 7. Variáveis de Ambiente

### Criar arquivo .env (opcional)
```bash
# services/api/.env
DATABASE_URL=postgresql://vivacampo:vivacampo@localhost:5432/vivacampo
REDIS_URL=redis://localhost:6379
AWS_ENDPOINT_URL=http://localhost:4566
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key-here
```

---

## 8. Resolver Erros do TypeScript

Os erros que você está vendo são **normais** e serão resolvidos após rodar:

```bash
cd services/app-ui
npm install

cd ../admin-ui
npm install
```

Isso vai instalar:
- `react` e `react-dom`
- `next`
- `axios`
- `leaflet`, `react-leaflet`
- `recharts`
- `zod`
- `@types/node`, `@types/react`, etc.

---

## 9. Estrutura de Portas

| Serviço | Porta | URL |
|---------|-------|-----|
| API | 8000 | http://localhost:8000 |
| Worker | - | Background |
| TiTiler | 8001 | http://localhost:8001 |
| App UI | 3002 | http://localhost:3002/app |
| Admin UI | 3001 | http://localhost:3001/admin |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| LocalStack | 4566 | http://localhost:4566 |

---

## 10. Troubleshooting

### Erro: "Cannot find module 'react'"
```bash
cd services/app-ui
npm install
```

### Erro: "Port already in use"
```bash
# Matar processo na porta
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Erro: "Database connection failed"
```bash
# Verificar se DB está rodando
docker compose ps db

# Reiniciar DB
docker compose restart db
```

### Erro: "Redis connection failed"
```bash
# Verificar se Redis está rodando
docker compose ps redis

# Reiniciar Redis
docker compose restart redis
```

---

## 11. Comandos Úteis

### Ver logs
```bash
# Todos serviços
docker compose logs -f

# Serviço específico
docker compose logs -f api
docker compose logs -f worker
```

### Parar tudo
```bash
docker compose down
```

### Limpar volumes (CUIDADO: apaga dados)
```bash
docker compose down -v
```

### Rebuild containers
```bash
docker compose up -d --build
```

### Rebuild & Clean (Recomendado)
Use o script utilitário para reconstruir e limpar automaticamente imagens antigas (`<none>`), evitando uso desnecessário de disco:

```powershell
.\rebuild.ps1
# Ou para um serviço específico:
.\rebuild.ps1 app_ui
# Ou sem cache (full rebuild):
.\rebuild.ps1 -NoCache
```

---

## 12. Próximos Passos

1. ✅ Instalar dependências (`npm install`)
2. ✅ Iniciar infraestrutura (`docker compose up -d db redis localstack`)
3. ✅ Aplicar migrations
4. ✅ Rodar API e Worker localmente
5. ✅ Rodar frontends (`npm run dev`)
6. ✅ Acessar http://localhost:3002 (App UI)
7. ✅ Acessar http://localhost:3001/admin (Admin UI)
8. ✅ Executar testes

---

## Status Atual

**Código:** ✅ 100% Completo  
**Dependências:** ⚠️ Precisam ser instaladas (`npm install`)  
**Infraestrutura:** ⚠️ Precisa ser iniciada (`docker compose up -d`)

**Após instalar dependências, todos os erros do TypeScript vão sumir!**
