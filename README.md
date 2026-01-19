# VivaCampo

Plataforma multi-tenant de Earth Observation para monitoramento agrícola via satélite.

## Início Rápido

### Pré-requisitos
- Docker Desktop
- Git

### Executar Localmente

```bash
# Clone o repositório
git clone <repo-url>
cd vivacampo-app

# Inicie os serviços
docker compose up -d

# Aguarde todos os serviços iniciarem (healthcheck do DB)
docker compose ps

# Acesse as interfaces
# Admin UI: http://localhost:3001/admin/
# App UI: http://localhost:3002/app/
# API: http://localhost:8000/docs
# TiTiler: http://localhost:8080/docs
```

### Aplicar Schema do Banco de Dados

```bash
# Conectar ao banco
docker compose exec db psql -U vivacampo -d vivacampo

# Aplicar migration
\i /path/to/infra/migrations/sql/001_initial_schema.sql

# Ou via comando direto
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/001_initial_schema.sql
```

### Verificar LocalStack

```bash
# Verificar S3 bucket
docker compose exec localstack awslocal s3 ls

# Verificar SQS queues
docker compose exec localstack awslocal sqs list-queues
```

## Estrutura do Projeto

```
vivacampo-app/
├── docker-compose.yml          # Orquestração de serviços
├── infra/
│   ├── docker/
│   │   ├── env/.env.local      # Variáveis de ambiente
│   │   └── localstack-init/    # Scripts de inicialização
│   └── migrations/sql/         # Migrations do banco
├── services/
│   ├── api/                    # FastAPI backend
│   ├── worker/                 # Python job processor
│   ├── tiler/                  # TiTiler (COG serving)
│   ├── admin-ui/               # Next.js admin interface
│   └── app-ui/                 # Next.js tenant interface
└── README.md
```

## Serviços

- **db** (PostgreSQL + PostGIS): Banco de dados principal
- **redis**: Cache e distributed locks
- **localstack**: Emulação S3 + SQS local
- **api**: Backend FastAPI (porta 8000)
- **worker**: Processador de jobs Python
- **tiler**: Servidor de tiles COG (porta 8080)
- **admin_ui**: Interface administrativa (porta 3001)
- **app_ui**: Interface de tenant (porta 3002)

## Desenvolvimento

Ver `implementation_plan.md` para detalhes completos da arquitetura e fases de implementação.

## Licença

Proprietary
