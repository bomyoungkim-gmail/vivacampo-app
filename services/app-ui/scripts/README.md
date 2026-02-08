# Scripts - VivaCampo App UI

Scripts utilitários para geração de assets e automação.

---

## 📦 `generate-ktx2.sh` & `compress-landing-assets.sh`

Gera texturas otimizadas para a aplicação.

- **`generate-ktx2.sh`**: Focado no Globo 3D (requer `basisu`).
- **`compress-landing-assets.sh`**: Focado na Landing Page. **Possui fallback automático para WebP/AVIF** caso `basisu` não esteja instalado.

### Uso

```bash
# Via npm script (recomendado)
npm run generate:ktx2

# Ou diretamente
bash scripts/generate-ktx2.sh
```

### Pré-requisitos

**Instalar `basisu` CLI:**

```bash
# Opção 1: Via npm
npm install -g @gltf-transform/cli

# Opção 2: Download direto
# https://github.com/BinomialLLC/basis_universal/releases
# Baixar executável e adicionar ao PATH
```

**Opcional: ImageMagick** (para gerar versão mobile)
```bash
# Ubuntu/Debian
sudo apt-get install imagemagick

# macOS
brew install imagemagick

# Windows
# https://imagemagick.org/script/download.php
```

### Output

O script gera os seguintes arquivos em `public/textures/compressed/`:

- **`earth_day.ktx2`** - Textura colorida principal (2048×1024)
- **`earth_day_mobile.ktx2`** - Versão LOD mobile (1024×512) *[se ImageMagick instalado]*
- **`earth_clouds.ktx2`** - Textura de nuvens com alpha (1024×512)

### Parâmetros de Compressão

```bash
-ktx2              # Formato de saída
-uastc             # Codec UASTC (melhor qualidade que ETC1s)
-uastc_level 2     # Nível de qualidade (0-4, padrão: 2)
-mipmap            # Gera mipmaps automaticamente
-y_flip            # Flip vertical (Three.js padrão)
-alpha             # Preserva canal alpha (apenas clouds)
```

### Troubleshooting

**Erro: `basisu: command not found`**
```bash
# Instalar ferramenta
npm install -g @gltf-transform/cli

# Verificar instalação
basisu --version
```

**Erro: Arquivo .ktx2 não gerado**
```bash
# Verificar se arquivos de origem existem
ls -lh public/textures/earth_*.{jpg,png}

# Executar com verbose
basisu -ktx2 -uastc -debug -output_file test.ktx2 public/textures/earth_day_2048.jpg
```

**Erro: "ImageMagick não instalado"**
- O script pula a geração da versão mobile
- Não é crítico (fallback para versão desktop)
- Instale ImageMagick se quiser otimização mobile máxima

---

## 📚 Documentação Relacionada

- [KTX2_COMPRESSION.md](../docs/KTX2_COMPRESSION.md) - Documentação completa
- [Basis Universal GitHub](https://github.com/BinomialLLC/basis_universal)
- [Three.js KTX2Loader](https://threejs.org/docs/#examples/en/loaders/KTX2Loader)

---

## ✅ Checklist de Uso

1. [ ] Instalar `basisu` CLI
2. [ ] (Opcional) Instalar ImageMagick
3. [ ] Executar `npm run generate:ktx2`
4. [ ] Verificar arquivos gerados: `ls public/textures/compressed/*.ktx2`
5. [ ] Testar no navegador: `npm run dev`
6. [ ] Validar logs no Console: "✅ KTX2 loaded: ..."
7. [ ] Commitar arquivos `.ktx2` ao repositório

---

**Última atualização:** 2025-02-07
