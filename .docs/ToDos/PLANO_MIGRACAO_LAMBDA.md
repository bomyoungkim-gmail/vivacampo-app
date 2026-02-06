# Análise e Plano de Simulação: Migração para AWS Lambda

## 1. Situação Atual (AS-IS)
Atualmente, o serviço `worker` funciona como um **Daemon Tradicional**.

*   **Infraestrutura:** Container Docker rodando 24/7.
*   **Código (`services/worker/worker/main.py`):**
    *   Possui um loop infinito (`while True`).
    *   Faz "polling" (perguntas constantes) à fila SQS: *"Tem mensagem? Tem mensagem?"*.
    *   Se a fila está vazia, o container continua rodando, consumindo CPU e Memória (e dinheiro, se fosse na nuvem) sem fazer nada.
*   **Problema para Lambda:** O AWS Lambda não suporta loops infinitos ou daemons. Ele precisa ser **invocado** por um evento e deve **terminar** quando o trabalho acabar.

## 2. Arquitetura Desejada (TO-BE: Event-Driven)
Mudança para o modelo **Serverless / Event-Driven**.

*   **Infraestrutura:** Função AWS Lambda "dorminte".
*   **Gatilho (Trigger):** O próprio serviço SQS da AWS "empurra" (push) a mensagem para o Lambda quando ela chega.
*   **Código Desejado:**
    *   Sem `while True`.
    *   Uma função única (`lambda_handler`) que recebe o `event` (contendo 1 ou mais mensagens) e o processa.
    *   O ciclo de vida é: `Acorda -> Processa -> Morre`.

## 3. Como Simular AWS Lambda Localmente?
Para desenvolver localmente com o mesmo comportamento da nuvem, usaremos o padrão **"Local Runner"**.

Como não temos o "Trigger do SQS" nativo rodando no seu PC (ele é um serviço interno da AWS), criaremos um script Python simples que **imita** esse comportamento.

### Componentes de Simulação:

#### A. O "AWS Fake" (LocalStack) 🏭
Você já tem isso no `docker-compose.yml`.
*   Ele sobe um SQS falso na porta `4566`.
*   Sua API envia mensagens para lá normalmente.

#### B. O Código do Lambda (O que vamos construir) 🧠
Vamos criar um adaptador que traduz o evento do Lambda para seus jobs existentes.

```python
# services/worker/worker/lambda_adapter.py
def handler(event, context):
    for record in event['Records']:
        msg_body = json.loads(record['body'])
        # Chama a lógica que já existe no seu projeto
        processar_job(msg_body)
```

#### C. O "Robô de Teste" (Local Runner) 🤖
Um script que só roda na sua máquina. Ele substitui o `while True` que antes ficava no código de produção.

**Fluxo do Local Runner:**
1.  Conecta no SQS do LocalStack.
2.  Lê mensagens (Long Polling).
3.  **Gerencia a Concorrência:** Utiliza um `ThreadPoolExecutor` para processar até **5 jobs simultâneos** (configurável), garantindo que sua máquina local não trave.
4.  **MONTA** um JSON igualzinho ao que a AWS Lambda enviaria (`{"Records": [...]}`).
5.  **INVOCA** sua função `handler` passando esse JSON.
6.  Repete.

---

## 4. Plano de Implementação

### Passo 1: Criar o Adapter
Criar `services/worker/worker/interface_lambda.py`.
Este arquivo será o ponto de entrada oficial na AWS.

### Passo 2: Criar o Runner Local
Criar `services/worker/run_local_lambda.py`.
Este script será usado por você no desenvolvimento (`python run_local_lambda.py`).

### Passo 3: Ajustar Docker Local (Opcional)
Podemos ajustar o `docker-compose.yml` para rodar esse `run_local_lambda.py` em vez do `main.py` antigo, garantindo que seu ambiente de dev seja 100% igual à arquitetura nova.

---

## 5. Benefícios desta Abordagem
1.  **Paridade Dev/Prod:** Você testa exatamente a função que vai para a nuvem.
2.  **Debug Fácil:** Como o *Runner* é apenas um script Python, você pode usar o debugger do VS Code normalmente.
3.  **Zero Risco:** A lógica de negócio (`jobs/process_week.py`, etc.) não muda nada. Só mudamos "quem chama" essa lógica.
