# AI Agents Usage Guide

This guide explains how to use the specialized AI agents configured for the VivaCampo project. These agents are designed to help you build and maintain the application following the Hexagonal Architecture.

## Available Agents

| Agent | Responsibility | When to Use |
|-------|----------------|-------------|
| **Domain Agent** | Core Business Logic | Creating Entities, Value Objects, Domain Services. Pure Python logic. |
| **Application Agent** | Use Cases & Flow | Implementing Use Cases, Commands, orchestration logic. |
| **Infrastructure Agent** | External Adapters | DB Repositories, API Clients, AWS integration. |
| **Presentation Agent** | API Surface | FastAPI routers, DTOs, Authentication. |
| **Test Agent** | Quality Assurance | Writing Pytest fixtures, integration tests with Testcontainers. |
| **Architecture Validator** | Code Compliance | Verifying dependency rules and layer boundaries. |
| **Security Validator** | Security Checking | Auditing RLS policies, SQL injection, and Multi-tenant isolation. |
| **Migration Agent** | Database Evolution | Safe schema changes and data migrations (Alembic). |
| **Documentation Agent** | Knowledge Capture | Writing ADRs, Docstrings, and Mermaid diagrams. |
| **Orchestrator Agent** | Coordination | Breaking down complex features and delegating to other agents. |

## How to Invoke an Agent

### In Antigravity (Gemini)

You can explicitly ask for a specific agent's expertise or let the system route it. To be precise, use the agent's name in your request.

**Examples:**
- "Using the **Domain Agent**, create a `CropCycle` entity."
- "Ask the **Infrastructure Agent** to implement the `INotificationService` using SES."
- "Run the **Security Validator** check on `app/infrastructure/repositories`."

### In Codex / Claude Code

The agents are configured as specific prompts/skills. You can load them into the context.

```bash
# Example (conceptual)
/load .codex/skills/domain-agent.md
/load .codex/skills/infrastructure-agent.md
```

## Workflows

### 1. New Feature Development
For a new feature like "Harvest Planning":

1.  **Start with Domain**: "Domain Agent, define the entities for Harvest Planning."
2.  **Move to App**: "Application Agent, create the `PlanHarvestCommand` and Use Case."
3.  **Build Infra**: "Infrastructure Agent, create a repository for Harvest plans."
4.  **Expose API**: "Presentation Agent, create the POST endpoint."
5.  **Verify**: "Test Agent, write an integration test for the whole flow."

### 2. Refactoring
1.  **Validate First**: "Architecture Validator, check the current dependencies of the Billing module."
2.  **Refactor**: "Application Agent, refactor this service to use the Command pattern."
3.  **Verify**: "Test Agent, ensure no regressions."

## Validation
Always run the validators after significant changes:

```bash
# Validate Architecture
python scripts/validate_architecture.py

# Validate Security
python scripts/validate_security.py
```
