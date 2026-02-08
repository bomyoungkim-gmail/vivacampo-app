#!/bin/bash
# ========================================
# Script de Geração KTX2 - Landing Page (Com Fallback)
# ========================================
# Tenta converter para KTX2. Se falhar, usa WebP/AVIF via sharp.
#
# Uso:
#   bash scripts/compress-landing-assets.sh

set -e

echo "🚀 Iniciando otimização de assets da Landing Page..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretórios
INPUT_DIR="public/landing"
OUTPUT_DIR="public/landing/compressed"
mkdir -p "$OUTPUT_DIR"

# Verificar se basisu existe via npx (node wrapper)
# O pacote `basis_universal` instala 'basisu' em .bin
# No Windows/Git Bash, precisamos checar node_modules/.bin/basisu.cmd ou basisu
if [ -f "./node_modules/.bin/basisu.cmd" ] || [ -f "./node_modules/.bin/basisu" ]; then
    echo "${GREEN}✅ basisu encontrado (npm)! Usando compressão KTX2.${NC}"
    MODE="ktx2"
       
    # Função wrapper para chamar via npx para garantir compatibilidade OS
    compress_cmd() {
       # Usar 'npx basisu' garante que usamos o binário correto do node_modules
       # e o wrapper cli.js lida com o .exe no Windows
       npx basisu "$@"
    }
elif command -v basisu &> /dev/null; then
    echo "${GREEN}✅ basisu encontrado no PATH!${NC}"
    MODE="ktx2"
    compress_cmd() {
        basisu "$@"
    }
else
    echo "${YELLOW}⚠️  basisu não encontrado. Usando fallback para WebP/AVIF (Sharp).${NC}"
    MODE="fallback"
fi

if [ "$MODE" == "ktx2" ]; then
    # ========================================
    # MODO KTX2 (Ideal)
    # ========================================
    process_file() {
        local input_file=$1
        local output_file=$2
        
        echo "📸 KTX2: Processando $(basename "$input_file")..."
        compress_cmd -ktx2 -uastc -uastc_level 2 -mipmap -y_flip -output_file "$output_file" "$input_file"
    }

    count=0
    # Processar JPG e PNG
    for img in "$INPUT_DIR"/*.{jpg,png}; do
        [ -e "$img" ] || continue
        filename=$(basename "$img" | sed 's/\.[^.]*$//')
        process_file "$img" "$OUTPUT_DIR/$filename.ktx2"
        count=$((count + 1))
    done

    if [ $count -eq 0 ]; then
        echo "${YELLOW}⚠️  Nenhum arquivo .png encontrado em $INPUT_DIR${NC}"
    else
        echo "${GREEN}✅ Geração KTX2 concluída para $count arquivos!${NC}"
    fi

else
    # ========================================
    # MODO FALLBACK (WebP/AVIF)
    # ========================================
    echo "📸 Iniciando conversão via Node.js (Sharp)..."
    
    if [ -f "scripts/compress-fallback.js" ]; then
        node scripts/compress-fallback.js
    else
        echo "${RED}❌ Erro: script de fallback não encontrado em scripts/compress-fallback.js${NC}"
        exit 1
    fi
fi

echo ""
echo "📁 Assets otimizados em: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR/"
echo ""
