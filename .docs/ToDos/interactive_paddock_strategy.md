# Estratégia: Fluxo Interativo de Divisão de Talhões e Qualidade de Dados

**Data:** 2026-02-05  
**Contexto:** Substituição do processamento monolítico de grandes áreas por um fluxo agronômico real de divisão de talhões, com camadas incrementais de inteligência.

---

## 1. Visão do Produto e Fluxo do Usuário (Fase 1: Estrutura)

Em vez de tentar processar uma "Fazenda" de 50.000 ha como uma imagem única, guiamos o usuário para modelar a realidade agrária.

### **Passo 1: Demarcação da Macro-Área**
*   O usuário desenha o perímetro total da fazenda.
*   **Sistema:** Aceita o polígono gigante, mas *não* inicia processamento ainda.

### **Passo 2: Pergunta de Intenção e Divisão**
*   **Interface:** "Você desenhou 10.000 ha. Como deseja dividir?"
*   **Opções:** Manual (Cut), Automático (Sugestão via Voronoi/Grid).

### **Passo 3: Ajuste Fino e Validação**
*   Usuário ajusta (Split/Merge).
*   **Validação:** Alerta se talhão > 2.000 ha (Limite Técnico).

### **Passo 4: Criação e Processamento Batch**
*   Cria N registros independentes.
*   Processa via Lambda (Batch) com 100% de resolução nativa.

---

## 2. Camada de Inteligência Incremental (Fase 2: Interatividade Agronômica)

Após ter os talhões definidos, adicionamos interatividade para transformar "Índices Relativos" em "Dados Absolutos".

### **Passo 5: Calibração de Campo (Ground Truth)**
*   **Problema:** O satélite vê proxies (NDVI 0.7), o produtor quer realidade (3.500 kg/ha). Sem calibração, temos apenas p10/p50/90 relativos.
*   **Interatividade:**
    *   Usuário seleciona um talhão e informa: "Nesta data, medi 3.500 kg MS/ha".
    *   Sistema registra: `{ talhao_id, data, valor_real, tipo: 'biomass' }`.
*   **Modelo de Correlação:**
    *   O backend cruza o `valor_real` com o `índice_satélite` da data.
    *   Gera uma **Curva de Regressão Personalizada** para aquela fazenda/variedade.
    *   *Resultado:* O mapa de cores relativas vira um mapa de "Estimativa de Colheita".

### **Passo 6: Estimativa Preditiva Regional (Contexto)**
*   **Problema:** O usuário novo não tem dados de campo ainda (Cold Start).
*   **Solução:** Usar inteligência de dados agregados.
    *   **Contexto:** Ao criar o talhão, o sistema identifica `Bioma: Cerrado`, `Estado: GO`, `Cultura: Soja`.
    *   **Predição:** "Historicamente, no Oeste Goiano, NDVI 0.75 em Fevereiro correlaciona com 65-70 sacas/ha."
*   **Aplicação:** O sistema exibe uma "Estimativa Projetada" baseada na média regional, até que o usuário insira seus próprios dados para refinar o modelo.

---

## 3. Estratégia Técnica e Stack Compliance

Para garantir viabilidade comercial sem custos de licenciamento, selecionamos bibliotecas Open Source permissivas (MIT/BSD).

### **Frontend & UX (MIT License)**
*   **Leiout/Mapa:** `Leaflet` (MIT) + `Leaflet-Geoman Free` (MIT).
    *   *Nota:* A versão Free do Geoman inclui Draw, Edit, Drag, e Delete. Recursos complexos como "Cut" podem ser implementados usando lógica própria com `Turf.js` se necessário, sem custo.
*   **Geometria Client-Side:** `Turf.js` (MIT).
    *   Líder de mercado para operações espaciais no navegador (Área, Interseção, Diferença).
*   **Visualização de Dados:** `Recharts` (MIT) e `TanStack Table` (MIT).
    *   Padrões da indústria para Dashboards React.

### **Backend & Science (BSD License)**
*   **Geometria:** `Shapely` (BSD-3-Clause).
    *   Padrão Python para manipulação geométrica.
*   **Matemática/Voronoi:** `SciPy` (BSD-3-Clause) e `NumPy` (BSD-3-Clause).
    *   Bibliotecas científicas fundamentais, livres para uso comercial.
*   **Machine Learning:** `Scikit-learn` (BSD-3-Clause).
    *   Para os modelos de regressão linear (calibração).

### **Endpoints Incrementais**
1.  `POST /v1/aois/simulate-split`: Sugestão de divisão (SciPy Voronoi).
2.  `POST /v1/field-data`: Registrar pesagem/colheita manual.
3.  `GET /v1/analytics/calibration`: Retorna modelo (R² e coeficientes).
4.  `GET /v1/analytics/prediction`: Retorna estimativa regional.

---

### Conclusão
A estratégia é tecnicamente robusta e **juridicamente segura**, utilizando stack 100% livre de royalties. O "Large AOI" deixa de ser um problema técnico e vira uma oportunidade de refinar o modelo agronômico do cliente.
