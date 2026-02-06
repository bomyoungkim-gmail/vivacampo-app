# Como Criar os Agentes - Guia Prático

## Visão Geral

Este guia mostra **3 formas** de implementar os agentes especializados:

1. **Prompts Customizados** (mais simples) - Arquivos markdown com instruções
2. **Scripts Python Interativos** (intermediário) - Scripts que chamam Claude API
3. **MCP Servers** (avançado) - Servidores Model Context Protocol

---

## Método 1: Prompts Customizados (Recomendado para Começar)

**Conceito**: Criar arquivos `.md` com instruções detalhadas que você copia/cola para Claude.

### Estrutura de Diretórios

```
.claude/
├── agent-prompts/
│   ├── domain-agent.md
│   ├── application-agent.md
│   ├── infrastructure-agent.md
│   ├── presentation-agent.md
│   └── test-agent.md
└── settings.local.json
```

### Passo 1: Criar Diretório

```bash
mkdir -p .claude/agent-prompts
```

### Passo 2: Criar Prompt do Domain Agent

**Arquivo**: `.claude/agent-prompts/domain-agent.md`

```markdown
# Domain Agent

You are a specialized Domain Agent for VivaCampo's hexagonal architecture.

## Your Role
Create Domain layer code: Entities, Value Objects, and Domain Services following DDD principles.

## Critical Rules

### 1. Technology Independence
- ❌ NEVER import: fastapi, sqlalchemy, boto3, requests, httpx
- ❌ NEVER import from: app.infrastructure, app.application, app.presentation
- ✅ ONLY pure Python and domain logic

### 2. Pydantic Configuration
ALL entities MUST use this exact configuration:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4

class Farm(BaseModel):
    """Domain Entity - Farm aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID  # ALWAYS required for multi-tenancy
    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=0, le=1000000)

    model_config = ConfigDict(
        validate_assignment=True,  # ← CRITICAL: Validates on EVERY assignment
        validate_default=True,
        str_strip_whitespace=True,
        extra="forbid",
        frozen=False
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if any(char in v for char in ['<', '>', '&']):
            raise ValueError("Name contains invalid characters")
        return v
```

### 3. Value Objects (Immutable)

```python
class Geometry(BaseModel):
    """Value Object - Immutable geometry"""
    type: str = Field(pattern="^(Point|Polygon|MultiPolygon)$")
    coordinates: list

    model_config = ConfigDict(frozen=True)  # ← IMMUTABLE

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Calculate bounding box - pure business logic"""
        # Implementation here
        pass
```

### 4. Domain Services (Pure Functions)

```python
class VegetationCalculatorService:
    """Domain Service - Pure business logic, no external dependencies"""

    def calculate_index(
        self,
        index_type: IndexType,
        bands: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Pure function - only math, no I/O"""
        if index_type == IndexType.NDVI:
            return self._calculate_ndvi(bands)
        elif index_type == IndexType.SAVI:
            return self._calculate_savi(bands)
        else:
            raise ValueError(f"Unsupported index: {index_type}")

    def _calculate_ndvi(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """NDVI = (NIR - Red) / (NIR + Red)"""
        nir = bands["nir"].astype(float)
        red = bands["red"].astype(float)
        return np.clip((nir - red) / (nir + red + 1e-10), -1.0, 1.0)
```

## Validation Checklist

Before providing code, verify:
- [ ] No imports from infrastructure/application/presentation layers
- [ ] All entities have `validate_assignment=True`
- [ ] All Value Objects have `frozen=True`
- [ ] `tenant_id` field present in all aggregate roots
- [ ] Field validators for all business rules
- [ ] Only pure business logic (no database, HTTP, file I/O)

## Example Usage

**User**: "Create a Farm entity with validation for minimum area of 1 hectare"

**Domain Agent Response**:
```python
# services/api/app/domain/entities/farm.py

from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4

class Farm(BaseModel):
    """
    Domain Entity - Farm aggregate root.

    Business Rules:
    - Minimum area: 1 hectare
    - Maximum area: 1,000,000 hectares
    - Name must be unique per tenant (validated in repository)
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=1.0, le=1000000.0)  # ← Business rule

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        str_strip_whitespace=True,
        extra="forbid"
    )

    @field_validator('area_hectares')
    @classmethod
    def validate_area(cls, v: float) -> float:
        """Enforce minimum area business rule"""
        if v < 1.0:
            raise ValueError("Farm area must be at least 1 hectare")
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize farm name"""
        if any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError("Farm name contains invalid characters")
        return v.strip()
```

✅ Validation passed:
- Uses `validate_assignment=True`
- Has `tenant_id` field
- Business rule (min area) enforced via Pydantic Field
- Additional validation in field_validator
- No external dependencies
```

## When to Use This Agent

Use the Domain Agent when you need to:
- Create new entities or value objects
- Add new domain services
- Implement business logic calculations
- Add validation rules
- Define domain exceptions

**Example prompts**:
- "Create a Crop entity with planting/harvest dates"
- "Add SAVI indicator calculation to VegetationCalculatorService"
- "Create a DateRange value object"
```

### Passo 3: Como Usar o Prompt

1. **Abrir Claude Code** ou **Claude Web**
2. **Copiar todo o conteúdo** de `.claude/agent-prompts/domain-agent.md`
3. **Colar como contexto** no início da conversa
4. **Fazer sua solicitação**: "Create a Crop entity with planting dates"

---

## Método 2: Scripts Python Interativos

**Conceito**: Scripts que chamam Claude API automaticamente com prompts especializados.

### Estrutura

```
.claude/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── domain_agent.py
│   ├── application_agent.py
│   └── infrastructure_agent.py
└── .env  # API keys
```

### Passo 1: Instalar Dependências

```bash
pip install anthropic python-dotenv
```

### Passo 2: Criar Base Agent

**Arquivo**: `.claude/agents/base_agent.py`

```python
"""
Base Agent - Classe base para todos os agentes especializados
"""

import os
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    """Classe base para agentes especializados"""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_history = []

    def generate(
        self,
        user_prompt: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096
    ) -> str:
        """
        Gera resposta usando Claude API.

        Args:
            user_prompt: Solicitação do usuário
            model: Modelo Claude a usar
            max_tokens: Máximo de tokens na resposta

        Returns:
            Resposta do agente
        """
        # Adicionar ao histórico
        self.conversation_history.append({
            "role": "user",
            "content": user_prompt
        })

        # Chamar API
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=self.system_prompt,
            messages=self.conversation_history
        )

        # Extrair resposta
        assistant_message = response.content[0].text

        # Adicionar ao histórico
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset(self):
        """Limpa histórico de conversa"""
        self.conversation_history = []

    def save_output(self, content: str, output_path: str):
        """Salva output em arquivo"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Output saved to: {output_path}")
```

### Passo 3: Criar Domain Agent

**Arquivo**: `.claude/agents/domain_agent.py`

```python
"""
Domain Agent - Agente especializado em Domain layer
"""

from .base_agent import BaseAgent

# Prompt do agente (mesmo conteúdo do .md)
DOMAIN_AGENT_PROMPT = """
You are a specialized Domain Agent for VivaCampo's hexagonal architecture.

RULES:
1. Domain layer MUST be technology-agnostic (no PostgreSQL, AWS, FastAPI)
2. ALL entities MUST use Pydantic BaseModel with validate_assignment=True
3. ALL fields MUST have validators for business rules
4. Entities MUST enforce invariants
5. Use Value Objects for complex domain concepts
6. Domain Services for complex business logic across multiple entities

PATTERNS TO FOLLOW:

**Entity Pattern**:
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4

class Farm(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid"
    )
```

VALIDATION CHECKLIST:
- [ ] No imports from infrastructure/application/presentation
- [ ] validate_assignment=True
- [ ] tenant_id present
- [ ] Field validators for business rules
"""

class DomainAgent(BaseAgent):
    """Agente especializado em criar código do Domain layer"""

    def __init__(self):
        super().__init__(
            name="Domain Agent",
            system_prompt=DOMAIN_AGENT_PROMPT
        )

    def create_entity(
        self,
        entity_name: str,
        description: str,
        fields: dict
    ) -> str:
        """
        Cria uma nova Domain Entity.

        Args:
            entity_name: Nome da entidade (ex: "Farm")
            description: Descrição da entidade
            fields: Dicionário com campos e tipos

        Returns:
            Código Python da entidade
        """
        prompt = f"""
Create a Domain Entity with the following specification:

Entity Name: {entity_name}
Description: {description}
Fields: {fields}

Generate complete Python code following Domain Agent patterns.
Include:
- Pydantic BaseModel with validate_assignment=True
- tenant_id field
- Field validators for business rules
- Docstrings
"""

        return self.generate(prompt)

    def create_value_object(
        self,
        vo_name: str,
        description: str
    ) -> str:
        """Cria um Value Object (imutável)"""
        prompt = f"""
Create a Value Object with the following specification:

Value Object Name: {vo_name}
Description: {description}

Generate complete Python code following Value Object pattern:
- Pydantic BaseModel with frozen=True (immutable)
- Business logic as @property methods
- No setters (immutable)
"""

        return self.generate(prompt)

    def create_domain_service(
        self,
        service_name: str,
        description: str,
        methods: list
    ) -> str:
        """Cria um Domain Service"""
        prompt = f"""
Create a Domain Service with the following specification:

Service Name: {service_name}
Description: {description}
Methods: {methods}

Generate complete Python code following Domain Service pattern:
- Pure business logic (no external dependencies)
- Pure functions (no side effects)
- Only mathematical calculations or domain rules
"""

        return self.generate(prompt)
```

### Passo 4: Criar Script CLI

**Arquivo**: `.claude/agents/cli.py`

```python
#!/usr/bin/env python3
"""
CLI para invocar agentes especializados
"""

import argparse
from pathlib import Path
from domain_agent import DomainAgent
# from application_agent import ApplicationAgent
# from infrastructure_agent import InfrastructureAgent

def main():
    parser = argparse.ArgumentParser(description="VivaCampo Agent CLI")
    parser.add_argument("agent", choices=["domain", "application", "infrastructure"])
    parser.add_argument("action", help="Action to perform (e.g., create-entity)")
    parser.add_argument("--name", help="Entity/Service name")
    parser.add_argument("--description", help="Description")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    # Selecionar agente
    if args.agent == "domain":
        agent = DomainAgent()
    else:
        print(f"Agent {args.agent} not implemented yet")
        return

    # Executar ação
    if args.action == "create-entity":
        if not args.name or not args.description:
            print("Error: --name and --description required")
            return

        print(f"🤖 {agent.name} creating entity '{args.name}'...\n")

        result = agent.create_entity(
            entity_name=args.name,
            description=args.description,
            fields={
                "name": "str",
                "area_hectares": "float"
            }
        )

        print(result)

        if args.output:
            agent.save_output(result, args.output)

    else:
        print(f"Action {args.action} not implemented")

if __name__ == "__main__":
    main()
```

### Passo 5: Usar o Script

```bash
# Criar Domain Entity
python .claude/agents/cli.py domain create-entity \
  --name "Crop" \
  --description "Crop planted in farm field" \
  --output "services/api/app/domain/entities/crop.py"

# Criar Value Object
python .claude/agents/cli.py domain create-value-object \
  --name "DateRange" \
  --description "Immutable date range"
```

---

## Método 3: MCP Servers (Avançado)

**Conceito**: Criar servidor MCP que expõe agentes como ferramentas.

### Estrutura

```
.claude/
├── mcp-servers/
│   ├── vivacampo-agents/
│   │   ├── server.py
│   │   ├── agents/
│   │   │   ├── domain_agent.py
│   │   │   └── ...
│   │   └── package.json
│   └── ...
└── settings.local.json
```

### Passo 1: Criar MCP Server

**Arquivo**: `.claude/mcp-servers/vivacampo-agents/server.py`

```python
#!/usr/bin/env python3
"""
MCP Server - Agentes VivaCampo
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Importar agentes
from agents.domain_agent import DomainAgent

# Inicializar server
server = Server("vivacampo-agents")

# Inicializar agentes
domain_agent = DomainAgent()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista ferramentas disponíveis"""
    return [
        Tool(
            name="create_domain_entity",
            description="Create a new Domain Entity following hexagonal architecture patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string"},
                    "description": {"type": "string"},
                    "fields": {"type": "object"}
                },
                "required": ["entity_name", "description"]
            }
        ),
        Tool(
            name="create_value_object",
            description="Create an immutable Value Object",
            inputSchema={
                "type": "object",
                "properties": {
                    "vo_name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["vo_name", "description"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa ferramenta (agente)"""

    if name == "create_domain_entity":
        result = domain_agent.create_entity(
            entity_name=arguments["entity_name"],
            description=arguments["description"],
            fields=arguments.get("fields", {})
        )

        return [TextContent(type="text", text=result)]

    elif name == "create_value_object":
        result = domain_agent.create_value_object(
            vo_name=arguments["vo_name"],
            description=arguments["description"]
        )

        return [TextContent(type="text", text=result)]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

### Passo 2: Configurar MCP no Claude Code

**Arquivo**: `.claude/settings.local.json`

```json
{
  "mcpServers": {
    "vivacampo-agents": {
      "command": "python",
      "args": [".claude/mcp-servers/vivacampo-agents/server.py"],
      "cwd": "c:/projects/vivacampo-app",
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

### Passo 3: Usar MCP Server no Claude Code

```
User: "Use the create_domain_entity tool to create a Crop entity"

Claude Code:
[Automatically calls MCP tool]
[Domain Agent generates code]
[Returns complete Entity implementation]
```

---

## Comparação dos Métodos

| Método | Complexidade | Velocidade | Automação | Melhor Para |
|--------|-------------|------------|-----------|-------------|
| **Prompts Customizados** | Baixa | Média | Manual | Começar rapidamente |
| **Scripts Python** | Média | Alta | Semi-auto | Uso frequente |
| **MCP Servers** | Alta | Muito Alta | Total | Integração profunda |

---

## Recomendação

**Para começar AGORA**:
1. Usar **Método 1** (Prompts Customizados)
2. Criar arquivos em `.claude/agent-prompts/`
3. Copiar/colar prompts quando precisar

**Depois de validar**:
1. Implementar **Método 2** (Scripts Python)
2. Automatizar tarefas repetitivas

**Para produção**:
1. Implementar **Método 3** (MCP Servers)
2. Integração total com Claude Code

---

## Próximos Passos

Vou criar os arquivos de prompt agora para você usar imediatamente!
