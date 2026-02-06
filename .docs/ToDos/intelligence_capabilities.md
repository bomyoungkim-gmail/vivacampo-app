# Menu de Inteligência Agronômica VivaCampo

**Objetivo:** Transformar "Dados Brutos" em "Inteligência de Negócio" usando o arsenal que já temos.

## 1. O Arsenal Atual (Índices Disponíveis)

### 🛰️ Ópticos (Monitoramento de Vigor)
Estes dependem de céu limpo (Sentinel-2).

| Índice | Nome Completo | O que ele vê? | Casos de Uso |
| :--- | :--- | :--- | :--- |
| **NDVI** | Normalized Difference Vegetation Index | Biomassa fotosinteticamente ativa. | Padrão ouro para saúde geral da lavoura. |
| **NDRE** | Normalized Difference Red Edge | Clorofila (sensível a mudanças sutis). | **Nitrogênio:** Detecta deficiência de N antes do NDVI "ver". |
| **RECI** | Red-Edge Chlorophyll Index | Conteúdo de Clorofila. | Ajuste fino de adubação nitrogenada. |
| **GNDVI** | Green NDVI | Vigor (usando banda Verde). | Bom para culturas muito densas (onde NDVI satura). |
| **EVI** | Enhanced Vegetation Index | Estrutura do dossel. | Melhor que NDVI em alta biomassa (soja fechada). |
| **SAVI** | Soil Adjusted Vegetation Index | Remove ruído do solo. | **Plantio:** Ideal para fases iniciais quando há muito solo exposto. |
| **ARI** | Anthocyanin Reflectance Index | Antocianina (pigmento de stress). | **Stress Precoce:** Detecta stress antes da clorofila degradar. |
| **CRI** | Carotenoid Reflectance Index | Carotenóides. | Indicador de senescência (envelhecimento) ou stress. |

### 💧 Água e Solo (Monitoramento Hídrico)
| Índice | Nome Completo | O que ele vê? | Casos de Uso |
| :--- | :--- | :--- | :--- |
| **NDMI** | Normalized Difference Moisture Index | Conteúdo de água na folha. | **Stress Hídrico:** A planta está "com sede"? |
| **MSI** | Moisture Stress Index | Stress hídrico invertido. | Outra visão para seca. |
| **NDWI** | Normalized Difference Water Index | Água em superfície. | Alagamentos, drenagem deficiente. |
| **BSI** | Bare Soil Index | Solo exposto. | Monitorar falhas de plantio ou colheita. |
| **NBR** | Normalized Burn Ratio | Carbonização/Seca extrema. | Detecção de queimadas ou resíduos secos. |

### 🦇 Radar (Sentinel-1) - "Visão Noturna"
Estes **atravessam nuvens**. É o seu trunfo para dias nublados.

| Métrica | O que é? | Inteligência Derivada |
| :--- | :--- | :--- |
| **RVI** | Radar Vegetation Index | Correlação com Biomassa. Substitui o NDVI quando está nublado (com menor precisão, mas mostra tendência). |
| **VH/VV** | Polarizações Cruzadas | Estrutura da planta. Detecta o **ponto de colheita** (quando a planta seca e muda a estrutura). |

---

## 2. Estratégias para "Dias Sem Dados" (Nublados)

Como exibir isso para o usuário sem causar confusão?

### A. UX para Dados de Radar (Sentinel-1)
Quando `Optical == NO_DATA`, o sistema ativa automaticamente o modo "Radar Fallback":

1.  **No Gráfico (Time Series):**
    *   Mantenha a linha do NDVI contínua.
    *   Nos pontos onde usamos Radar (RVI), mude o estilo da linha para **pontilhado** ou os pontos para um ícone "vazado" (⚪).
    *   *Tooltip:* "Dado estimado via Radar (cobertura de nuvens)."

2.  **No Mapa:**
    *   Exiba a camada RVI com uma paleta de cores similar ao NDVI (Red-Yellow-Green), mas com **menor saturação** (cores lavadas).
    *   Adicione um **Overlay (Marca d'água)** discreto no canto: *"Modo Radar / Estimativa"*.
    *   Isso educa o usuário que aquele dado é uma tendência de biomassa, não uma "foto" óptica perfeita.

### B. Interpolação Linear (Tendência)
Preencher "buracos" de até 10-15 dias usando matemática simples.
*   *Visualização:* Uma linha cinza tracejada conectando os dois pontos reais de NDVI.
*   *Valor:* "Estimado". Isso evita que o gráfico despenque para zero, o que assustaria o usuário.

---

## 3. Inteligência via Time Series e Correlações
O diferencial competitivo: sair do "O que aconteceu?" para "Por que aconteceu?".

### A. Dashboard de Correlação Hídrica (Causa e Efeito)
Cruzar dados de Vigor (NDVI) com Clima (Chuva/ET0) no mesmo eixo temporal.
*   **Visual:** Gráfico Combo.
    *   Eixo Y Esquerdo (Linha): NDVI (Vigor da Planta).
    *   Eixo Y Direito (Barras Azuis): Precipitação Acumulada.
*   **Insight:** O usuário vê visualmente o *Lag* (atraso): *"Parou de chover dia 10, o NDVI começou a cair dia 25."* -> DIAGNÓSTICO: Stress Hídrico confirmado.

### B. Comparação de Safra (Year-over-Year)
*   **Funcionalidade:** "Como estava meu talhão hoje, no ano passado?"
*   **Visual:** Duas linhas no gráfico.
    *   Linha Verde Sólida: Safra Atual (2025/26).
    *   Linha Cinza Tracejada: Safra Anterior (2024/25).
*   **Inteligência:** Se a linha verde cruzar para baixo da cinza, gera um **Alerta de Quebra de Produtividade**.

### C. Integral da Curva (Produtividade Estimada)
*   A "boca do jacaré" (área abaixo da curva de NDVI ao longo do ciclo) tem altíssima correlação com a produtividade final (sacas/ha).
*   **Feature:** Exibir um "Score de Potencial Produtivo" acumulado.
    *   *"Sua safra acumulou 15% mais biomassa que a média histórica até o momento."*

---

## 4. Oportunidades Científicas (Estado da Arte 2024-2025)

Pesquisa recente (IEEE, MDPI) aponta caminhos que vão além do básico:

### A. Estimativa de Nitrogênio (SRRE)
*   **A Ciência:** O índice **NDRE** é bom, mas o **SRRE (Simple Ratio Red Edge)** mostrou correlação superior (R² > 0.8) para absorção de Nitrogênio em milho e arroz.
*   **Fórmula:** `NIR / RedEdge` (sem normalização).
*   **Ação:** Implementar SRRE no worker (temos as bandas).
*   **Produto:** "Mapa de Recomendação de Ureia" (Variable Rate Nitrogen).

### B. Detecção de Colheita via Radar (VH Backscatter)
*   **A Ciência:** O coeficiente de retroespalhamento (Backscatter) da polarização **VH** cai abruptamente (> 3dB) quando a cultura é colhida, pois a estrutura do solo exposto reflete menos que a planta.
*   **Ação:** Monitorar a derivada da curva VH. Se `VH_Hoje - VH_SemanaPassada < -3dB`, marcar como "Provável Colheita".
*   **Produto:** "Alerta de Colheita Realizada" (útil para Tradings e Bancos monitorarem garantias).

### C. Predição de Produtividade (Fusion ML)
*   **A Ciência:** Modelos de *Random Forest* que usam **(NDVI Médio + NDRE Médio + Chuva Acumulada + Chuva na Florada)** acertam a produtividade com erro menor que 10%.
*   **Ação:** Criar um modelo tabular simples (Scikit-Learn) treinado com histórico.
*   **Produto:** "Estimativa de Sacas/Ha" (atualizada semanalmente).

---

## 5. Features Sugeridas ("Low Hanging Fruit")

Considerando o que já temos implementado no backend:

1.  **Detector de Deficiência de Nitrogênio:** Usar **NDRE** e **RECI** (que temos e quase ninguém usa) para alertar: *"Vigor alto (NDVI), mas Clorofila caindo (NDRE). Possível falta de Nitrogênio."*
2.  **Monitoramento de Colheita (Radar):** Usar a banda **VH** do Radar para detectar a queda brusca de rugosidade que indica colheita, mesmo com chuva.
