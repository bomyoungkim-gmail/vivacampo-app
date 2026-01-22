# Documentação de Indicadores de Monitoramento

Este documento fornece especificações técnicas, aplicações agronômicas e guias de interpretação para os 14 índices de monitoramento disponíveis na plataforma VivaCampo.

> **Nota:** Todos os índices são processados internamente utilizando bandas espectrais brutas dos satélites Sentinel-2 (Óptico) e Sentinel-1 (Radar). 
> As fórmulas abaixo correspondem às implementações padrão da literatura científica e repositórios de sensoriamento remoto (ex: Sentinel Hub Custom Scripts).

---

## 1. Saúde e Vigor (Plant Health)

Focados no desenvolvimento vegetativo, biomassa e atividade fotossintética.

### **NDVI (Normalized Difference Vegetation Index)**
*   **Nome:** Índice de Vegetação da Diferença Normalizada
*   **Fórmula:** `(NIR - Red) / (NIR + Red)`
*   **Bandas:** B8, B4
*   **Aplicação:** Monitoramento geral de vigor e distinção entre vegetação/solo.
*   **Interpretação:**
    *   `< 0.2`: Solo exposto ou água.
    *   `0.2 - 0.5`: Vegetação esparsa ou fase inicial.
    *   `> 0.6`: Vegetação densa e saudável.
*   **Fonte da Fórmula:** [Sentinel Hub - NDVI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/ndvi/)

### **NDRE (Normalized Difference Red Edge)**
*   **Nome:** Índice de Borda Vermelha
*   **Fórmula:** `(NIR - RedEdge) / (NIR + RedEdge)`
*   **Bandas:** B8, B5
*   **Aplicação:** Detecção precoce de estresse e monitoramento em dosséis densos.
*   **Interpretação:** Similar ao NDVI, mas não satura tão rápido. Quedas neste índice muitas vezes precedem quedas visuais no NDVI.
*   **Fonte da Fórmula:** [Index Database - NDRE](https://www.indexdatabase.de/db/i-single.php?id=223)

### **GNDVI (Green NDVI)**
*   **Nome:** NDVI Verde
*   **Fórmula:** `(NIR - Green) / (NIR + Green)`
*   **Bandas:** B8, B3
*   **Aplicação:** Avaliação de taxas fotossintéticas e absorção de água/nutrientes.
*   **Interpretação:** Mais sensível à clorofila ativa do que à biomassa estrutural.
*   **Fonte da Fórmula:** [Sentinel Hub - GNDVI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/gndvi/)

### **EVI (Enhanced Vegetation Index)**
*   **Nome:** Índice de Vegetação Melhorado
*   **Fórmula:** `2.5 * ((NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1))`
*   **Bandas:** B8, B4, B2
*   **Aplicação:** Áreas de altíssima densidade (milho fechado, cana, florestas).
*   **Interpretação:** Valores tendem a ser mais baixos que o NDVI, mas mantêm sensibilidade onde o NDVI ficaria "plano" no máximo.
*   **Fonte da Fórmula:** [Sentinel Hub - EVI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/evi/)

### **RECI (Red-Edge Chlorophyll Index)**
*   **Nome:** Índice de Clorofila Red-Edge
*   **Fórmula:** `(NIR / RedEdge) - 1`
*   **Bandas:** B8, B5
*   **Aplicação:** Estimativa direta de clorofila foliar (proxy para Nitrogênio).
*   **Interpretação:** Valores altos indicam folhas ricas em nitrogênio e saudáveis. Quedas indicam clorose.
*   **Fonte da Fórmula:** [Index Database - CIred-edge](https://www.indexdatabase.de/db/i-single.php?id=128)

---

## 2. Status Hídrico (Water Status)

Monitoramento do conteúdo de água na planta e no solo.

### **NDWI (Normalized Difference Water Index)**
*   **Nome:** Índice de Água
*   **Fórmula:** `(Green - NIR) / (Green + NIR)` (McFeeters)
*   **Bandas:** B3, B8
*   **Aplicação:** Detecção de corpos d'água e alagamentos.
*   **Interpretação:**
    *   `> 0`: Água líquida presente (alagamento).
    *   `< 0`: Superfícies sem água livre (vegetação ou solo).
*   **Fonte da Fórmula:** [Sentinel Hub - NDWI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/ndwi/)

### **NDMI (Normalized Difference Moisture Index)**
*   **Nome:** Índice de Umidade
*   **Fórmula:** `(NIR - SWIR) / (NIR + SWIR)`
*   **Bandas:** B8, B11
*   **Aplicação:** Estresse hídrico na cultura (seca agrícola).
*   **Interpretação:**
    *   `Valores Altos`: Planta turgida, sem estresse hídrico.
    *   `Valores Baixos`: Estresse hídrico, fechamento de estômatos.
*   **Fonte da Fórmula:** [Sentinel Hub - NDMI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/ndmi/)

### **MSI (Moisture Stress Index)**
*   **Nome:** Índice de Estresse Hídrico
*   **Fórmula:** `SWIR / NIR`
*   **Bandas:** B11, B8
*   **Aplicação:** Inverso do NDMI, focado na severidade da seca.
*   **Interpretação:**
    *   `> 1.6`: Estresse hídrico severo.
    *   `< 0.6`: Planta bem hidratada.
*   **Fonte da Fórmula:** [Index Database - MSI](https://www.indexdatabase.de/db/i-single.php?id=51)

---

## 3. Nutrição e Pigmentos (Nutrition)

### **ARI (Anthocyanin Reflectance Index)**
*   **Nome:** Índice de Antocianina
*   **Fórmula:** `(1 / Green) - (1 / RedEdge)`
*   **Bandas:** B3, B5
*   **Aplicação:** Estresse por frio, salinidade ou deficiência de Fósforo.
*   **Interpretação:** Aumento do índice indica acúmulo de pigmentos de estresse (folhas arroxeadas).
*   **Fonte da Fórmula:** [Index Database - ARI](https://www.indexdatabase.de/db/i-single.php?id=7)

### **CRI (Carotenoid Reflectance Index)**
*   **Nome:** Índice de Carotenoides
*   **Fórmula:** `(1 / Blue) - (1 / Green)` (CRI2)
*   **Bandas:** B2, B3
*   **Aplicação:** Senescência, envelhecimento ou estresse oxidativo.
*   **Interpretação:** Aumento indica degradação da clorofila (amarelecimento).
*   **Fonte da Fórmula:** [Index Database - CRI 2](https://www.indexdatabase.de/db/i-single.php?id=126)

---

## 4. Solo e Fogo (Soil & Fire)

### **SAVI (Soil Adjusted Vegetation Index)**
*   **Nome:** Índice Ajustado ao Solo
*   **Fórmula:** `((NIR - Red) / (NIR + Red + L)) * (1 + L)` (L=0.428)
*   **Bandas:** B8, B4
*   **Aplicação:** Fases iniciais de plantio.
*   **Interpretação:** Similar ao NDVI, mas mais preciso quando há muito solo visível entre as plantas.
*   **Fonte da Fórmula:** [Sentinel Hub - SAVI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/savi/)

### **NBR (Normalized Burn Ratio)**
*   **Nome:** Razão de Queimada
*   **Fórmula:** `(NIR - SWIR2) / (NIR + SWIR2)`
*   **Bandas:** B8, B12
*   **Aplicação:** Detecção de áreas queimadas.
*   **Interpretação:** Quedas drásticas indicam ocorrência de fogo ou colheita com queima.
*   **Fonte da Fórmula:** [Sentinel Hub - NBR](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/nbr/)

### **BSI (Bare Soil Index)**
*   **Nome:** Índice de Solo Exposto
*   **Fórmula:** `((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))`
*   **Bandas:** B11, B4, B8, B2
*   **Aplicação:** Detecção de falhas de plantio ou erosão.
*   **Interpretação:** Valores altos indicam ausência total de cobertura vegetal.
*   **Fonte da Fórmula:** [Sentinel Hub - BSI](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/barren_soil/)

---

## 5. Radar (Sentinel-1)

Monitoramento independente de nuvens (All-Weather).

### **RVI (Radar Vegetation Index - Dual Pol)**
*   **Nome:** Índice de Vegetação por Radar
*   **Fórmula:** `4 * VH / (VV + VH)`
*   **Bandas:** Sentinel-1 VV, VH
*   **Aplicação:** Estimativa de biomassa sob nuvens.
*   **Interpretação:**
    *   `0 - 0.3`: Solo nu.
    *   `> 0.6`: Vegetação desenvolvida.
*   **Fonte da Fórmula:** [Sentinel Hub - SAR-Index](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-1/sar-index/) (Adaptado para Dual Pol)

### **Razão VH/VV**
*   **Aplicação:** Mudanças estruturais (tombamento, floração).
*   **Interpretação:** Varia conforme a geometria/arquitetura da cultura específica.
*   **Fonte da Fórmula:** Literatura padrão de sensoriamento remoto por radar.
