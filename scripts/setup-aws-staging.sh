#!/bin/bash
# VivaCampo - AWS Staging Setup Script
# Este script automatiza o provisionamento inicial da infraestrutura AWS

set -e  # Exit on error

echo "🚀 VivaCampo AWS Staging Setup"
echo "================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para erro
error() {
    echo -e "${RED}❌ ERRO: $1${NC}"
    exit 1
}

# Função para sucesso
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Função para aviso
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Verificar dependências
echo "📋 Verificando dependências..."
command_exists aws || error "AWS CLI não instalado. Instale: https://aws.amazon.com/cli/"
command_exists terraform || error "Terraform não instalado. Instale: https://www.terraform.io/downloads"
command_exists docker || error "Docker não instalado. Instale: https://www.docker.com/get-started"
command_exists psql || warning "psql não instalado. Você precisará dele para aplicar migrações."
success "Todas as dependências instaladas"

# 2. Verificar credenciais AWS
echo ""
echo "🔑 Verificando credenciais AWS..."
if ! aws sts get-caller-identity &>/dev/null; then
    error "Credenciais AWS não configuradas. Execute: aws configure"
fi
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-sa-east-1}
success "Credenciais AWS válidas (Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION)"

# 3. Confirmar custos
echo ""
echo "💰 ATENÇÃO: Este script vai criar recursos PAGOS na AWS"
echo "   Estimativa de custo mensal: ~\$50-65 USD"
echo "   - RDS db.t3.micro: ~\$15-20"
echo "   - ECS Fargate: ~\$30-40"
echo "   - S3/CloudWatch: ~\$5"
echo ""
read -p "Deseja continuar? (digite 'sim' para confirmar): " confirm
if [ "$confirm" != "sim" ]; then
    echo "Setup cancelado pelo usuário."
    exit 0
fi

# 4. Criar bucket para Terraform state (se não existir)
echo ""
echo "📦 Configurando Terraform state..."
TERRAFORM_BUCKET="vivacampo-terraform-state"
if ! aws s3 ls "s3://$TERRAFORM_BUCKET" 2>/dev/null; then
    echo "Criando bucket S3 para Terraform state..."
    aws s3 mb "s3://$TERRAFORM_BUCKET" --region "$AWS_REGION"
    aws s3api put-bucket-versioning \
        --bucket "$TERRAFORM_BUCKET" \
        --versioning-configuration Status=Enabled
    success "Bucket Terraform state criado: $TERRAFORM_BUCKET"
else
    success "Bucket Terraform state já existe: $TERRAFORM_BUCKET"
fi

# 5. Criar repositórios ECR
echo ""
echo "🐳 Criando repositórios ECR..."
REPOS=("api" "worker" "tiler" "app-ui" "admin-ui")
for repo in "${REPOS[@]}"; do
    REPO_NAME="vivacampo-$repo"
    if ! aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$AWS_REGION" &>/dev/null; then
        aws ecr create-repository \
            --repository-name "$REPO_NAME" \
            --region "$AWS_REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        success "Repositório ECR criado: $REPO_NAME"
    else
        success "Repositório ECR já existe: $REPO_NAME"
    fi
done

# 6. Gerar senha segura para DB
echo ""
echo "🔐 Gerando senha do banco de dados..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -base64 32)

# 7. Criar secrets no AWS Secrets Manager
echo ""
echo "🔒 Criando secrets no AWS Secrets Manager..."
if ! aws secretsmanager describe-secret --secret-id vivacampo/staging/db-password --region "$AWS_REGION" &>/dev/null; then
    aws secretsmanager create-secret \
        --name vivacampo/staging/db-password \
        --secret-string "$DB_PASSWORD" \
        --region "$AWS_REGION"
    success "Secret criado: vivacampo/staging/db-password"
else
    success "Secret já existe: vivacampo/staging/db-password"
fi

if ! aws secretsmanager describe-secret --secret-id vivacampo/staging/jwt-secret --region "$AWS_REGION" &>/dev/null; then
    aws secretsmanager create-secret \
        --name vivacampo/staging/jwt-secret \
        --secret-string "$JWT_SECRET" \
        --region "$AWS_REGION"
    success "Secret criado: vivacampo/staging/jwt-secret"
else
    success "Secret já existe: vivacampo/staging/jwt-secret"
fi

# 8. Obter VPC default e subnets
echo ""
echo "🌐 Obtendo informações da VPC default..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region "$AWS_REGION")
if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
    error "VPC default não encontrada. Crie uma VPC ou use uma existente."
fi
success "VPC default encontrada: $VPC_ID"

SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region "$AWS_REGION")
SUBNET_ARRAY=($SUBNET_IDS)
if [ ${#SUBNET_ARRAY[@]} -lt 2 ]; then
    error "Pelo menos 2 subnets são necessárias para RDS Multi-AZ. Encontradas: ${#SUBNET_ARRAY[@]}"
fi
success "Subnets encontradas: ${SUBNET_ARRAY[0]}, ${SUBNET_ARRAY[1]}"

SG_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region "$AWS_REGION")
success "Security Group default: $SG_ID"

# 9. Criar arquivo terraform.tfvars
echo ""
echo "📝 Criando terraform.tfvars..."
cd terraform/staging
cat > terraform.tfvars <<EOF
aws_region = "$AWS_REGION"
db_name = "vivacampo"
db_username = "vivacampo"
db_password = "$DB_PASSWORD"
db_subnet_ids = ["${SUBNET_ARRAY[0]}", "${SUBNET_ARRAY[1]}"]
db_security_group_ids = ["$SG_ID"]
EOF
success "terraform.tfvars criado"

# 10. Terraform init e apply
echo ""
echo "🏗️  Provisionando infraestrutura com Terraform..."
terraform init
terraform plan -out=tfplan
echo ""
warning "Revise o plano acima. Recursos serão criados na AWS."
read -p "Aplicar plano? (digite 'sim' para confirmar): " confirm_tf
if [ "$confirm_tf" != "sim" ]; then
    echo "Terraform apply cancelado."
    exit 0
fi

terraform apply tfplan
success "Infraestrutura provisionada com sucesso!"

# 11. Obter outputs do Terraform
echo ""
echo "📊 Obtendo informações da infraestrutura..."
RDS_ENDPOINT=$(terraform output -raw rds_endpoint 2>/dev/null || echo "N/A")
S3_BUCKET_TILES=$(terraform output -raw s3_bucket_tiles 2>/dev/null || echo "N/A")
SQS_QUEUE_URL=$(terraform output -raw sqs_queue_jobs 2>/dev/null || echo "N/A")

# 12. Aplicar migrações SQL
echo ""
echo "🗄️  Aplicando migrações SQL no RDS..."
if [ "$RDS_ENDPOINT" != "N/A" ]; then
    echo "Endpoint RDS: $RDS_ENDPOINT"
    echo "Aguardando RDS ficar disponível (pode levar 5-10 minutos)..."
    aws rds wait db-instance-available --region "$AWS_REGION" 2>/dev/null || true
    
    echo ""
    echo "Execute manualmente as migrações:"
    echo "  psql -h $RDS_ENDPOINT -U vivacampo -d vivacampo"
    echo "  Senha: (veja AWS Secrets Manager: vivacampo/staging/db-password)"
    echo ""
    echo "Depois, dentro do psql:"
    echo "  \\i infra/migrations/sql/001_initial_schema.sql"
    echo "  \\i infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql"
    echo "  \\i infra/migrations/sql/003_add_ai_assistant_tables.sql"
    echo "  \\i infra/migrations/sql/004_add_ai_assistant_indexes.sql"
    echo "  \\i infra/migrations/sql/005_enable_rls.sql"
    echo "  \\i infra/migrations/sql/006_add_tenant_query_indexes.sql"
    echo "  \\i infra/migrations/sql/007_add_stac_scene_cache.sql"
    echo "  \\i infra/migrations/sql/008_add_aoi_parent_and_field_calibrations.sql"
else
    warning "RDS endpoint não disponível. Verifique Terraform outputs."
fi

# 13. Build e push de imagens Docker
echo ""
echo "🐳 Build e push de imagens Docker..."
read -p "Fazer build e push das imagens agora? (s/n): " build_images
if [ "$build_images" == "s" ]; then
    cd ../..  # Voltar para raiz do projeto
    
    # Login no ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Build
    docker compose build api worker tiler app-ui admin-ui
    
    # Tag e push
    for repo in "${REPOS[@]}"; do
        docker tag "vivacampo-$repo:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/vivacampo-$repo:staging"
        docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/vivacampo-$repo:staging"
        success "Imagem pushed: vivacampo-$repo:staging"
    done
fi

# 14. Resumo final
echo ""
echo "================================"
echo "🎉 Setup concluído com sucesso!"
echo "================================"
echo ""
echo "📋 Próximos passos:"
echo "1. Aplicar migrações SQL no RDS (veja instruções acima)"
echo "2. Criar ECS services (via Terraform ou AWS Console)"
echo "3. Configurar GitHub Secrets para CI/CD:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION=$AWS_REGION"
echo ""
echo "📊 Recursos criados:"
echo "   - RDS Endpoint: $RDS_ENDPOINT"
echo "   - S3 Bucket (tiles): $S3_BUCKET_TILES"
echo "   - SQS Queue: $SQS_QUEUE_URL"
echo "   - ECR Repositories: vivacampo-{api,worker,tiler,app-ui,admin-ui}"
echo ""
echo "🔐 Secrets criados no AWS Secrets Manager:"
echo "   - vivacampo/staging/db-password"
echo "   - vivacampo/staging/jwt-secret"
echo ""
echo "💰 Lembrete: Recursos AWS estão ATIVOS e gerando custos (~\$50-65/mês)"
echo "   Para destruir: cd terraform/staging && terraform destroy"
echo ""
