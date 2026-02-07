# VivaCampo - AWS Staging Setup Script (Windows PowerShell)
# Este script automatiza o provisionamento inicial da infraestrutura AWS

$ErrorActionPreference = "Stop"

Write-Host "🚀 VivaCampo AWS Staging Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Função para verificar se comando existe
function Test-Command {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# 1. Verificar dependências
Write-Host "📋 Verificando dependências..." -ForegroundColor Yellow
if (-not (Test-Command aws)) {
    Write-Host "❌ AWS CLI não instalado. Instale: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}
if (-not (Test-Command terraform)) {
    Write-Host "❌ Terraform não instalado. Instale: https://www.terraform.io/downloads" -ForegroundColor Red
    exit 1
}
if (-not (Test-Command docker)) {
    Write-Host "❌ Docker não instalado. Instale: https://www.docker.com/get-started" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Todas as dependências instaladas" -ForegroundColor Green

# 2. Verificar credenciais AWS
Write-Host ""
Write-Host "🔑 Verificando credenciais AWS..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    $AWS_ACCOUNT_ID = $identity.Account
    $AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "sa-east-1" }
    Write-Host "✅ Credenciais AWS válidas (Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Credenciais AWS não configuradas. Execute: aws configure" -ForegroundColor Red
    exit 1
}

# 3. Confirmar custos
Write-Host ""
Write-Host "💰 ATENÇÃO: Este script vai criar recursos PAGOS na AWS" -ForegroundColor Yellow
Write-Host "   Estimativa de custo mensal: ~`$50-65 USD"
Write-Host "   - RDS db.t3.micro: ~`$15-20"
Write-Host "   - ECS Fargate: ~`$30-40"
Write-Host "   - S3/CloudWatch: ~`$5"
Write-Host ""
$confirm = Read-Host "Deseja continuar? (digite 'sim' para confirmar)"
if ($confirm -ne "sim") {
    Write-Host "Setup cancelado pelo usuário."
    exit 0
}

# 4. Criar bucket para Terraform state
Write-Host ""
Write-Host "📦 Configurando Terraform state..." -ForegroundColor Yellow
$TERRAFORM_BUCKET = "vivacampo-terraform-state"
try {
    aws s3 ls "s3://$TERRAFORM_BUCKET" 2>$null | Out-Null
    Write-Host "✅ Bucket Terraform state já existe: $TERRAFORM_BUCKET" -ForegroundColor Green
}
catch {
    Write-Host "Criando bucket S3 para Terraform state..."
    aws s3 mb "s3://$TERRAFORM_BUCKET" --region $AWS_REGION
    aws s3api put-bucket-versioning --bucket $TERRAFORM_BUCKET --versioning-configuration Status=Enabled
    Write-Host "✅ Bucket Terraform state criado: $TERRAFORM_BUCKET" -ForegroundColor Green
}

# 5. Criar repositórios ECR
Write-Host ""
Write-Host "🐳 Criando repositórios ECR..." -ForegroundColor Yellow
$REPOS = @("api", "worker", "tiler", "app-ui", "admin-ui")
foreach ($repo in $REPOS) {
    $REPO_NAME = "vivacampo-$repo"
    try {
        aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION 2>$null | Out-Null
        Write-Host "✅ Repositório ECR já existe: $REPO_NAME" -ForegroundColor Green
    }
    catch {
        aws ecr create-repository `
            --repository-name $REPO_NAME `
            --region $AWS_REGION `
            --image-scanning-configuration scanOnPush=true `
            --encryption-configuration encryptionType=AES256
        Write-Host "✅ Repositório ECR criado: $REPO_NAME" -ForegroundColor Green
    }
}

# 6. Gerar senhas seguras
Write-Host ""
Write-Host "🔐 Gerando senhas seguras..." -ForegroundColor Yellow
$DB_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 25 | ForEach-Object {[char]$_})
$JWT_SECRET = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes(-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})))

# 7. Criar secrets no AWS Secrets Manager
Write-Host ""
Write-Host "🔒 Criando secrets no AWS Secrets Manager..." -ForegroundColor Yellow
try {
    aws secretsmanager describe-secret --secret-id vivacampo/staging/db-password --region $AWS_REGION 2>$null | Out-Null
    Write-Host "✅ Secret já existe: vivacampo/staging/db-password" -ForegroundColor Green
}
catch {
    aws secretsmanager create-secret `
        --name vivacampo/staging/db-password `
        --secret-string $DB_PASSWORD `
        --region $AWS_REGION
    Write-Host "✅ Secret criado: vivacampo/staging/db-password" -ForegroundColor Green
}

try {
    aws secretsmanager describe-secret --secret-id vivacampo/staging/jwt-secret --region $AWS_REGION 2>$null | Out-Null
    Write-Host "✅ Secret já existe: vivacampo/staging/jwt-secret" -ForegroundColor Green
}
catch {
    aws secretsmanager create-secret `
        --name vivacampo/staging/jwt-secret `
        --secret-string $JWT_SECRET `
        --region $AWS_REGION
    Write-Host "✅ Secret criado: vivacampo/staging/jwt-secret" -ForegroundColor Green
}

# 8. Obter VPC default e subnets
Write-Host ""
Write-Host "🌐 Obtendo informações da VPC default..." -ForegroundColor Yellow
$VPC_ID = (aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
if ([string]::IsNullOrEmpty($VPC_ID) -or $VPC_ID -eq "None") {
    Write-Host "❌ VPC default não encontrada. Crie uma VPC ou use uma existente." -ForegroundColor Red
    exit 1
}
Write-Host "✅ VPC default encontrada: $VPC_ID" -ForegroundColor Green

$SUBNET_IDS = (aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region $AWS_REGION) -split '\s+'
if ($SUBNET_IDS.Count -lt 2) {
    Write-Host "❌ Pelo menos 2 subnets são necessárias. Encontradas: $($SUBNET_IDS.Count)" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Subnets encontradas: $($SUBNET_IDS[0]), $($SUBNET_IDS[1])" -ForegroundColor Green

$SG_ID = (aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)
Write-Host "✅ Security Group default: $SG_ID" -ForegroundColor Green

# 9. Criar arquivo terraform.tfvars
Write-Host ""
Write-Host "📝 Criando terraform.tfvars..." -ForegroundColor Yellow
Set-Location terraform\staging
@"
aws_region = "$AWS_REGION"
db_name = "vivacampo"
db_username = "vivacampo"
db_password = "$DB_PASSWORD"
db_subnet_ids = ["$($SUBNET_IDS[0])", "$($SUBNET_IDS[1])"]
db_security_group_ids = ["$SG_ID"]
"@ | Out-File -FilePath terraform.tfvars -Encoding UTF8
Write-Host "✅ terraform.tfvars criado" -ForegroundColor Green

# 10. Terraform init e apply
Write-Host ""
Write-Host "🏗️  Provisionando infraestrutura com Terraform..." -ForegroundColor Yellow
terraform init
terraform plan -out=tfplan
Write-Host ""
Write-Host "⚠️  Revise o plano acima. Recursos serão criados na AWS." -ForegroundColor Yellow
$confirm_tf = Read-Host "Aplicar plano? (digite 'sim' para confirmar)"
if ($confirm_tf -ne "sim") {
    Write-Host "Terraform apply cancelado."
    exit 0
}

terraform apply tfplan
Write-Host "✅ Infraestrutura provisionada com sucesso!" -ForegroundColor Green

# 11. Resumo final
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🎉 Setup concluído com sucesso!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Aplicar migrações SQL no RDS"
Write-Host "2. Criar ECS services (via Terraform ou AWS Console)"
Write-Host "3. Configurar GitHub Secrets para CI/CD"
Write-Host ""
Write-Host "💰 Lembrete: Recursos AWS estão ATIVOS e gerando custos (~`$50-65/mês)" -ForegroundColor Yellow
Write-Host "   Para destruir: cd terraform\staging; terraform destroy"
Write-Host ""
