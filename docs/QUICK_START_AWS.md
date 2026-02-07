# Guia Rápido: Deploy AWS - VivaCampo MVP

## 🎯 TL;DR - O que está faltando?

**Você NÃO está fazendo nada errado!** O código está pronto. Falta apenas:
1. **Credenciais AWS** (criar usuário IAM)
2. **Provisionar infraestrutura** (executar Terraform)
3. **Aplicar migrações SQL** (no RDS após provisionamento)

**Custo estimado:** ~$50-65/mês para ambiente de staging

---

## ⚡ Opção 1: Setup Automatizado (Recomendado)

### Windows (PowerShell)
```powershell
# 1. Configurar credenciais AWS
aws configure
# Preencha: Access Key ID, Secret Access Key, Region (sa-east-1)

# 2. Executar script de setup
cd c:\projects\vivacampo-app
.\scripts\setup-aws-staging.ps1
```

### Linux/Mac (Bash)
```bash
# 1. Configurar credenciais AWS
aws configure

# 2. Executar script de setup
cd /path/to/vivacampo-app
chmod +x scripts/setup-aws-staging.sh
./scripts/setup-aws-staging.sh
```

**O script vai:**
- ✅ Criar bucket S3 para Terraform state
- ✅ Criar repositórios ECR para Docker images
- ✅ Gerar senhas seguras e salvar no AWS Secrets Manager
- ✅ Provisionar RDS, ECS, S3, SQS via Terraform
- ✅ (Opcional) Build e push de imagens Docker

---

## ⚡ Opção 2: Setup Manual (Passo a Passo)

### Fase 1: Credenciais AWS (15 min)
```bash
# 1. Criar usuário IAM na AWS Console
# IAM → Users → Create User → Attach policies:
#   - AmazonECS_FullAccess
#   - AmazonRDS_FullAccess
#   - AmazonS3_FullAccess
#   - AmazonSQS_FullAccess

# 2. Gerar Access Key
# User → Security credentials → Create access key

# 3. Configurar AWS CLI
aws configure
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: sa-east-1
# Default output format: json
```

### Fase 2: Provisionar Infraestrutura (30 min)
```bash
cd terraform/staging

# 1. Criar terraform.tfvars
cat > terraform.tfvars <<EOF
aws_region = "sa-east-1"
db_name = "vivacampo"
db_username = "vivacampo"
db_password = "SENHA_SEGURA_AQUI"  # Gere uma senha forte
db_subnet_ids = ["subnet-xxxxx", "subnet-yyyyy"]  # Obtenha via: aws ec2 describe-subnets
db_security_group_ids = ["sg-xxxxx"]  # Obtenha via: aws ec2 describe-security-groups
EOF

# 2. Inicializar Terraform
terraform init

# 3. Revisar plano
terraform plan

# 4. Aplicar (CRIA RECURSOS PAGOS!)
terraform apply
```

### Fase 3: Aplicar Migrações SQL (15 min)
```bash
# 1. Obter endpoint RDS
terraform output rds_endpoint
# Exemplo: vivacampo-staging.xxxxx.sa-east-1.rds.amazonaws.com

# 2. Conectar ao RDS
psql -h vivacampo-staging.xxxxx.sa-east-1.rds.amazonaws.com -U vivacampo -d vivacampo

# 3. Aplicar migrações (em ordem)
\i infra/migrations/sql/001_initial_schema.sql
\i infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql
\i infra/migrations/sql/003_add_ai_assistant_tables.sql
\i infra/migrations/sql/004_add_ai_assistant_indexes.sql
\i infra/migrations/sql/005_enable_rls.sql
\i infra/migrations/sql/006_add_tenant_query_indexes.sql
\i infra/migrations/sql/007_add_stac_scene_cache.sql
\i infra/migrations/sql/008_add_aoi_parent_and_field_calibrations.sql
```

### Fase 4: Deploy de Imagens (30 min)
```bash
# 1. Criar repositórios ECR
aws ecr create-repository --repository-name vivacampo-api --region sa-east-1
aws ecr create-repository --repository-name vivacampo-worker --region sa-east-1
aws ecr create-repository --repository-name vivacampo-tiler --region sa-east-1

# 2. Login no ECR
aws ecr get-login-password --region sa-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com

# 3. Build
docker compose build api worker tiler

# 4. Tag
docker tag vivacampo-api:latest <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com/vivacampo-api:staging
docker tag vivacampo-worker:latest <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com/vivacampo-worker:staging
docker tag vivacampo-tiler:latest <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com/vivacampo-tiler:staging

# 5. Push
docker push <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com/vivacampo-api:staging
docker push <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com/vivacampo-worker:staging
docker push <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com/vivacampo-tiler:staging
```

### Fase 5: Criar ECS Services (via Console AWS)
1. ECS → Clusters → Create Cluster → `vivacampo-staging`
2. Create Service → Launch type: Fargate
3. Task Definition: Create new (use imagens ECR)
4. Configurar variáveis de ambiente (DB_HOST, S3_BUCKET, etc)

---

## 📋 Checklist de Verificação

Antes de provisionar AWS:
- [ ] Tenho cartão de crédito cadastrado na AWS
- [ ] Entendo que vou gastar ~$50-65/mês
- [ ] Tenho credenciais AWS configuradas (`aws sts get-caller-identity` funciona)
- [ ] Revisei o plano Terraform (`terraform plan`)

Após provisionar:
- [ ] RDS está disponível (status: available)
- [ ] Migrações SQL aplicadas com sucesso
- [ ] Imagens Docker pushed para ECR
- [ ] ECS tasks rodando (status: RUNNING)
- [ ] Health check OK: `curl https://staging-api.vivacampo.com/health`

---

## 🆘 Troubleshooting

### Erro: "Credenciais AWS inválidas"
```bash
# Verificar credenciais
aws sts get-caller-identity

# Reconfigurar
aws configure
```

### Erro: "Terraform backend não inicializado"
```bash
# Criar bucket S3 para state
aws s3 mb s3://vivacampo-terraform-state --region sa-east-1

# Inicializar
terraform init
```

### Erro: "RDS não conecta"
```bash
# Verificar security group permite conexão na porta 5432
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Adicionar regra se necessário
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --cidr 0.0.0.0/0  # ATENÇÃO: Apenas para teste! Use IP específico em produção
```

### Erro: "Docker push falha"
```bash
# Re-login no ECR
aws ecr get-login-password --region sa-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.sa-east-1.amazonaws.com
```

---

## 💰 Estimativa de Custos Detalhada

| Recurso | Tipo | Custo/Hora | Custo/Mês | Notas |
|---------|------|------------|-----------|-------|
| RDS PostgreSQL | db.t3.micro | $0.034 | $24.48 | 730h/mês |
| ECS Fargate (API) | 0.5 vCPU, 1GB RAM | $0.024 | $17.52 | 730h/mês |
| ECS Fargate (Worker) | 0.5 vCPU, 1GB RAM | $0.024 | $17.52 | 730h/mês |
| S3 Storage | 10 GB | - | $0.23 | $0.023/GB |
| S3 Requests | 100k GET | - | $0.04 | $0.0004/1k |
| SQS | 1M requests | - | $0.00 | Grátis até 1M |
| CloudWatch Logs | 5 GB | - | $2.50 | $0.50/GB |
| **TOTAL** | | | **~$62/mês** | |

**Dicas para reduzir custos:**
- Use RDS Snapshot antes de parar (economiza ~$15/mês quando não usar)
- Configure Auto Scaling para ECS (escala para 0 à noite)
- Ative S3 Lifecycle para deletar tiles antigos (>30 dias)

---

## 🚀 Próximos Passos Após Deploy

1. **Configurar CI/CD:**
   - GitHub → Settings → Secrets → Add:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_REGION`
   - Push para `develop` → Deploy automático

2. **Configurar Monitoramento:**
   - CloudWatch Alarms para error rate
   - CloudWatch Dashboard para métricas
   - SNS para notificações

3. **Configurar Backup:**
   - RDS Automated Backups (7 dias)
   - S3 Versioning para tiles
   - Snapshot manual antes de mudanças grandes

4. **Validar Funcionalidades:**
   - Criar AOI de teste
   - Verificar processamento de jobs
   - Validar tiles renderizando
   - Testar autenticação OIDC

---

## 📚 Referências

- **Diagnóstico completo:** `diagnostico_deploy_aws.md`
- **Script automatizado (Windows):** `scripts/setup-aws-staging.ps1`
- **Script automatizado (Linux/Mac):** `scripts/setup-aws-staging.sh`
- **Runbook de deploy:** `docs/runbooks/deploy.md`
- **Terraform staging:** `terraform/staging/`
- **Migrações SQL:** `infra/migrations/sql/`

---

**Última atualização:** 2026-02-06
