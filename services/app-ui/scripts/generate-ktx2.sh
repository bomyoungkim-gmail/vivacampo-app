#!/bin/bash
# ========================================
# Script de Geração KTX2 - VivaCampo
# ========================================
# Converte texturas JPG/PNG para formato KTX2 com compressão Basis Universal
#
# Requisitos:
#   - basisu CLI: https://github.com/BinomialLLC/basis_universal
#   - Instalar: npm install -g basisu-cli
#
# Uso:
#   bash scripts/generate-ktx2.sh

set -e

echo "🚀 Gerando texturas KTX2 para o globo terrestre..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretórios
INPUT_DIR="public/textures"
OUTPUT_DIR="public/textures/compressed"
mkdir -p "$OUTPUT_DIR"

# Verificar se basisu existe via npx (node wrapper) ou PATH
if [ -f "./node_modules/.bin/basisu.cmd" ] || [ -f "./node_modules/.bin/basisu" ]; then
    echo "✅ basisu encontrado (npm)! Usando compressão KTX2."
    compress_cmd() {
       npx basisu "$@"
    }
elif command -v basisu &> /dev/null; then
    echo "✅ basisu encontrado no PATH!"
    compress_cmd() {
        basisu "$@"
    }
else
    echo "❌ basisu não encontrado!"
    echo "📦 Certifique-se de ter rodado: npm install"
    exit 1
fi

# ========================================
# Earth Day Texture (Color Map)
# ========================================
echo ""
echo "${YELLOW}📸 Processando earth_day_2048.jpg...${NC}"

compress_cmd \
    -ktx2 \
    -uastc \
    -uastc_level 2 \
    -mipmap \
    -y_flip \
    -output_file "$OUTPUT_DIR/earth_day.ktx2" \
    "$INPUT_DIR/earth_day_2048.jpg"

echo "${GREEN}✅ earth_day.ktx2 gerado!${NC}"

# ========================================
# Earth Clouds Texture (Alpha Map)
# ========================================
echo ""
echo "${YELLOW}☁️  Processando earth_clouds_1024.png...${NC}"

compress_cmd \
    -ktx2 \
    -uastc \
    -uastc_level 2 \
    -mipmap \
    -y_flip \
    -output_file "$OUTPUT_DIR/earth_clouds.ktx2" \
    "$INPUT_DIR/earth_clouds_1024.png"

echo "${GREEN}✅ earth_clouds.ktx2 gerado!${NC}"

# ========================================
# LOD Versions (Optional - Mobile)
# ========================================
echo ""
echo "${YELLOW}📱 Gerando versão LOD para mobile (1024x512)...${NC}"

# Criar versão reduzida temporária com ImageMagick (se disponível)
if command -v convert &> /dev/null; then
    convert "$INPUT_DIR/earth_day_2048.jpg" -resize 1024x512 /tmp/earth_day_1024.jpg

    compress_cmd \
        -ktx2 \
        -uastc \
        -uastc_level 1 \
        -mipmap \
        -y_flip \
        -output_file "$OUTPUT_DIR/earth_day_mobile.ktx2" \
        /tmp/earth_day_1024.jpg

    rm /tmp/earth_day_1024.jpg
    echo "${GREEN}✅ earth_day_mobile.ktx2 gerado!${NC}"
else
    echo "${YELLOW}⚠️  ImageMagick não instalado. Pulando versão mobile.${NC}"
    echo "   Instale com: apt-get install imagemagick (Linux) ou brew install imagemagick (Mac)"
fi

# ========================================
# Resumo
# ========================================
echo ""
echo "=================================================="
echo "✅ GERAÇÃO COMPLETA!"
echo "=================================================="
echo ""
echo "📁 Arquivos gerados em: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR"/*.ktx2
echo ""
echo "📊 Comparação de Tamanho:"
ORIGINAL_SIZE=$(du -sh "$INPUT_DIR/earth_day_2048.jpg" | cut -f1)
COMPRESSED_SIZE=$(du -sh "$OUTPUT_DIR/earth_day.ktx2" | cut -f1)
echo "   Original (JPG):    $ORIGINAL_SIZE"
echo "   Comprimido (KTX2): $COMPRESSED_SIZE"
echo ""
echo "🎯 Próximos Passos:"
echo "   1. Atualizar EarthGlobe.tsx para usar .ktx2"
echo "   2. Configurar KTX2Loader no Three.js"
echo "   3. Testar no navegador (Chrome DevTools > Rendering > Texture Compression)"
echo ""
