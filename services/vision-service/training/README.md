# VivaCampo Vision - Training Guide

## Modelos Disponíveis

### 1. Detecção de Doenças em Culturas (Crop Disease)
- **Backbone**: EfficientNetV2-S (ImageNet-21k)
- **Input**: 384x384 RGB
- **Doenças suportadas**: Soja, Milho, Café, Citros, Algodão, Cana, Pastagem

### 2. Estimativa de Peso de Gado (Cattle/Swine Weight)
- **Backbone**: EfficientNetV2-S
- **Outputs**: Peso (kg) + Body Condition Score (BCS 1-9)
- **Animais**: Bovinos, Suínos

### 3. Saúde Animal (Livestock Health)
- **Bovinos**: 16 condições (pneumonia, mastite, foot rot, etc.)
- **Suínos**: 12 condições (PRRS, erisipela, etc.)
- **Aves**: 12 condições (respiratórias, parasitárias, nutricionais)

---

## Datasets Públicos Recomendados

### Para Doenças em Culturas

| Dataset | Imagens | Classes | URL |
|---------|---------|---------|-----|
| PlantVillage | 54,306 | 38 | [Kaggle](https://www.kaggle.com/datasets/emmarex/plantdisease) |
| Plant Leaves | 4,500+ | 22 | [Mendeley](https://data.mendeley.com/datasets/hb74ynkjcn/1) |
| PlantDoc | 2,598 | 27 | [GitHub](https://github.com/pratikkayal/PlantDoc-Dataset) |

### Para Peso/Saúde de Gado

| Dataset | Descrição | URL |
|---------|-----------|-----|
| Roboflow Universe | Cattle detection datasets | [Roboflow](https://universe.roboflow.com/search?q=cattle) |
| Open Images | Animal detection | [OpenImages](https://storage.googleapis.com/openimages/web/index.html) |

### Datasets Brasileiros (institucionais)

- **Embrapa**: Datasets de doenças em soja, milho e outras culturas
- **CNPGC**: Dados de gado Nelore e outras raças brasileiras
- **UFV/UFLA/Esalq**: Pesquisas com datasets agrícolas

---

## Como Treinar

### 1. Preparar Ambiente

```bash
cd services/vision-service
pip install -r requirements.txt
pip install tensorflow-hub albumentations
```

### 2. Organizar Dataset

**Para Classificação (doenças):**
```
data/
├── doenca_1/
│   ├── img001.jpg
│   ├── img002.jpg
├── doenca_2/
│   ├── img003.jpg
├── saudavel/
│   ├── img004.jpg
```

**Para Estimativa de Peso:**
```
data/
├── images/
│   ├── cow001.jpg
│   ├── cow002.jpg
├── annotations.json
```

Formato do `annotations.json`:
```json
{
  "samples": [
    {
      "image": "images/cow001.jpg",
      "weight_kg": 450.0,
      "bcs": 5,
      "breed": "Nelore",
      "age_months": 24
    }
  ]
}
```

### 3. Download Modelos Base

```bash
# Listar modelos disponíveis
python training/download_pretrained.py --list-models

# Listar datasets públicos
python training/download_pretrained.py --list-datasets

# Criar modelos base para fine-tuning
python training/download_pretrained.py --setup all --output-dir ./pretrained
```

### 4. Treinar Modelo de Classificação

```bash
python training/train_classifier.py \
  --data-dir ./data/crop_diseases \
  --output-dir ./outputs/crop_disease \
  --model-name soja_diseases \
  --backbone efficientnetv2-s \
  --image-size 384 \
  --batch-size 32 \
  --epochs 100 \
  --learning-rate 1e-4 \
  --use-class-weights
```

### 5. Treinar Modelo de Peso

```bash
python training/train_weight_estimator.py \
  --data-dir ./data/cattle_weight \
  --output-dir ./outputs/cattle_weight \
  --model-name nelore_weight \
  --backbone efficientnetv2-s \
  --image-size 384 \
  --batch-size 32 \
  --epochs 100
```

### 6. Exportar para TFLite (Mobile)

```bash
# Exportar todas as variantes de quantização
python training/export_tflite.py \
  ./outputs/crop_disease/model_best.keras \
  --output-dir ./tflite/crop_disease \
  --quantization all \
  --representative-data ./data/crop_diseases \
  --benchmark

# Exportar apenas INT8 (menor tamanho)
python training/export_tflite.py \
  ./outputs/cattle_weight/model_best.keras \
  --output-dir ./tflite/cattle_weight \
  --quantization int8 \
  --representative-data ./data/cattle_weight
```

---

## Tipos de Quantização TFLite

| Tipo | Tamanho | Velocidade | Uso |
|------|---------|------------|-----|
| none | 100% | Base | Desenvolvimento |
| dynamic | ~25% | Mais rápido | Geral |
| float16 | ~50% | Rápido | GPU mobile |
| int8 | ~25% | Mais rápido | CPU mobile |

**Recomendado para mobile**: `dynamic` ou `int8`

---

## Métricas Esperadas

### Detecção de Doenças
- **Accuracy**: >85% (com dataset balanceado)
- **F1-Score**: >0.80 por classe

### Estimativa de Peso
- **MAE**: <30 kg para bovinos, <10 kg para suínos
- **BCS Accuracy**: >70%

### Saúde Animal
- **Accuracy**: >80%
- **Sensibilidade**: >85% (detectar doença é crítico)

---

## Dicas de Treinamento

1. **Data Augmentation**: Sempre use para aumentar generalização
2. **Class Weights**: Use para datasets desbalanceados
3. **Transfer Learning**: Comece com backbone pré-treinado
4. **Fine-tuning gradual**: Primeiro treine só a cabeça, depois desfreeze backbone
5. **Early Stopping**: Evita overfitting
6. **Learning Rate Schedule**: Reduza LR quando val_loss estabilizar

---

## Estrutura de Arquivos de Saída

```
outputs/
├── crop_disease/
│   ├── model_20240101_120000_best.keras
│   ├── model_20240101_120000_final.keras
│   ├── model_20240101_120000_history.csv
│   ├── model_20240101_120000_config.json
│   ├── class_mapping.json
│   └── logs/
│       └── model_20240101_120000/
│           └── events.out.tfevents.*

tflite/
├── crop_disease/
│   ├── model.tflite
│   ├── model_dynamic.tflite
│   ├── model_float16.tflite
│   ├── model_int8.tflite
│   └── model_conversion_report.json
```
