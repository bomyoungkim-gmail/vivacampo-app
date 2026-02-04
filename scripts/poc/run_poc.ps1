# PoC: Dynamic Tiling Latency Test
# Execute este script para testar a viabilidade do Dynamic Tiling + MosaicJSON

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PoC: Dynamic Tiling Latency Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Python está instalado
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Python não encontrado. Instale Python 3.11+" -ForegroundColor Red
    exit 1
}

# Criar venv se não existir
$venvPath = ".\.venv-poc"
if (-not (Test-Path $venvPath)) {
    Write-Host "Criando virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Ativar venv
Write-Host "Ativando virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Instalar dependências
Write-Host "Instalando dependências..." -ForegroundColor Yellow
pip install -q -r requirements-poc.txt

# Executar teste
Write-Host ""
Write-Host "Executando teste de latência..." -ForegroundColor Green
Write-Host ""

python test_dynamic_tiling_latency.py

# Desativar venv
deactivate

Write-Host ""
Write-Host "Teste concluído!" -ForegroundColor Green
