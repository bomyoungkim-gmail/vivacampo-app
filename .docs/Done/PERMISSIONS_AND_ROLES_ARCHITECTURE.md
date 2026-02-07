# Arquitetura de Permissões e Roles - VivaCampo

## Visão Geral

Sistema de permissões **customizável por convite**, onde o TENANT_ADMIN escolhe o nível de acesso de cada usuário convidado.

---

## Roles Disponíveis

### 1. **SYSTEM_ADMIN** (Super Admin)
```python
UserRole.SYSTEM_ADMIN
```

**Escopo**: Todo o sistema
**Quem é**: Administrador da plataforma VivaCampo

**Permissões**:
- ✅ Gerenciar todos os tenants
- ✅ Ver estatísticas globais
- ✅ Suspender/ativar tenants
- ✅ Configurar sistema
- ✅ Acessar qualquer recurso de qualquer tenant

**Quando usar**: Apenas para equipe interna da VivaCampo

---

### 2. **TENANT_ADMIN** (Administrador do Tenant)
```python
UserRole.TENANT_ADMIN
```

**Escopo**: Seu tenant
**Quem é**: Primeiro usuário que se cadastra (owner)

**Permissões**:
- ✅ **Fazendas**: Criar/editar/apagar TODAS as fazendas do tenant
- ✅ **Usuários**: Convidar usuários com diferentes roles (VIEWER ou EDITOR)
- ✅ **Billing**: Gerenciar plano, billing, Stripe
- ✅ **Configurações**: Custom rules, alertas, integrações
- ✅ **Visualização**: Ver todos os dados do tenant
- ⚠️ **Requer email verificado**: Para convidar usuários e fazer upgrade

**Quando usar**: Owner da fazenda/cooperativa/consultoria

---

### 3. **EDITOR** (Usuário Colaborador)
```python
UserRole.EDITOR
```

**Escopo**: Recursos que ele criou + visualização geral
**Quem é**: Usuário convidado com permissão de edição

**Permissões**:
- ✅ **Criar fazendas**: Dentro do limite do plano
- ✅ **Editar fazendas**: Apenas fazendas que ELE criou
- ✅ **Apagar fazendas**: Apenas fazendas que ELE criou
- ✅ **Ver fazendas**: TODAS as fazendas do tenant (somente leitura nas que não criou)
- ✅ **Criar alertas**: Para fazendas que ele criou
- ❌ **Convidar usuários**: Não pode
- ❌ **Gerenciar billing**: Não pode
- ❌ **Editar fazendas de outros**: Não pode

**Quando usar**: Agricultor em cooperativa, consultor em empresa de consultoria, membro de equipe

---

### 4. **VIEWER** (Usuário Somente Leitura)
```python
UserRole.VIEWER
```

**Escopo**: Apenas visualização
**Quem é**: Usuário convidado com acesso somente leitura

**Permissões**:
- ✅ **Ver fazendas**: Todas as fazendas do tenant (somente leitura)
- ✅ **Ver imagens**: Imagens de satélite, índices (NDVI, SAVI)
- ✅ **Ver alertas**: Alertas do tenant
- ✅ **Exportar relatórios**: (se disponível no plano)
- ❌ **Criar fazendas**: Não pode
- ❌ **Editar fazendas**: Não pode
- ❌ **Apagar fazendas**: Não pode
- ❌ **Criar alertas**: Não pode
- ❌ **Convidar usuários**: Não pode

**Quando usar**: Investidor, auditor, cliente (em consultoria), trainee

---

## Tabela de Permissões

| Ação | SYSTEM_ADMIN | TENANT_ADMIN | EDITOR | VIEWER |
|------|--------------|--------------|--------|--------|
| **Fazendas** |
| Criar fazenda | ✅ | ✅ | ✅ (limite do plano) | ❌ |
| Editar fazenda (própria) | ✅ | ✅ | ✅ | ❌ |
| Editar fazenda (de outros) | ✅ | ✅ | ❌ | ❌ |
| Apagar fazenda (própria) | ✅ | ✅ | ✅ | ❌ |
| Apagar fazenda (de outros) | ✅ | ✅ | ❌ | ❌ |
| Ver fazendas do tenant | ✅ | ✅ | ✅ | ✅ |
| **Alertas** |
| Criar alerta (fazenda própria) | ✅ | ✅ | ✅ | ❌ |
| Criar alerta (fazenda de outros) | ✅ | ✅ | ❌ | ❌ |
| Ver alertas | ✅ | ✅ | ✅ | ✅ |
| **Usuários** |
| Convidar usuários | ✅ | ✅ (se email verificado) | ❌ | ❌ |
| Remover usuários | ✅ | ✅ | ❌ | ❌ |
| Alterar role de usuários | ✅ | ✅ | ❌ | ❌ |
| **Billing** |
| Ver plano atual | ✅ | ✅ | ✅ | ✅ |
| Fazer upgrade de plano | ✅ | ✅ (se email verificado) | ❌ | ❌ |
| Configurar Stripe | ✅ | ✅ (se email verificado) | ❌ | ❌ |
| **Configurações** |
| Custom rules globais | ✅ | ✅ | ❌ | ❌ |
| Configurações do tenant | ✅ | ✅ | ❌ | ❌ |
| **Visualização** |
| Ver imagens de satélite | ✅ | ✅ | ✅ | ✅ |
| Ver índices (NDVI, SAVI) | ✅ | ✅ | ✅ | ✅ |
| Exportar relatórios | ✅ | ✅ | ✅ | ✅ (se plano permite) |

---

## Implementação - Domain Layer

### 1. Atualizar UserRole Enum

**Arquivo**: `services/api/app/domain/entities/user.py`

```python
# services/api/app/domain/entities/user.py

from enum import Enum

class UserRole(str, Enum):
    """Roles de usuário com níveis de permissão"""

    # Admin global (equipe VivaCampo)
    SYSTEM_ADMIN = "system_admin"

    # Admin do tenant (owner)
    TENANT_ADMIN = "tenant_admin"

    # Usuário colaborador (pode criar/editar suas fazendas)
    EDITOR = "editor"

    # Usuário somente leitura (pode apenas visualizar)
    VIEWER = "viewer"
```

### 2. Adicionar Campo `created_by_user_id` em Farm

**Arquivo**: `services/api/app/domain/entities/farm.py`

```python
# services/api/app/domain/entities/farm.py

from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4

class Farm(BaseModel):
    """Domain Entity - Farm aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID  # SEMPRE required para multi-tenancy
    created_by_user_id: UUID  # Usuário que criou (para permissões de EDITOR)

    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=0, le=1000000)
    # ... outros campos

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid"
    )

    def can_edit(self, user_id: UUID, user_role: UserRole) -> bool:
        """
        Verifica se usuário pode editar esta fazenda.

        Business Rules:
        - SYSTEM_ADMIN: pode editar qualquer fazenda
        - TENANT_ADMIN: pode editar qualquer fazenda do tenant
        - EDITOR: pode editar apenas fazendas que ELE criou
        - VIEWER: não pode editar nenhuma fazenda
        """
        if user_role == UserRole.SYSTEM_ADMIN:
            return True

        if user_role == UserRole.TENANT_ADMIN:
            return True

        if user_role == UserRole.EDITOR:
            return self.created_by_user_id == user_id

        return False  # VIEWER não pode editar
```

---

## Implementação - Application Layer

### Use Case: Criar Fazenda (Com Ownership)

**Arquivo**: `services/api/app/application/use_cases/farms/create_farm.py`

```python
# services/api/app/application/use_cases/farms/create_farm.py

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.domain.entities.farm import Farm
from app.domain.entities.user import UserRole
from app.domain.repositories.farm_repository import IFarmRepository
from app.application.exceptions import QuotaExceededError, PermissionDeniedError

class CreateFarmCommand(BaseModel):
    """Command para criar fazenda"""
    tenant_id: UUID
    user_id: UUID  # ← Usuário que está criando
    user_role: UserRole  # ← Role do usuário

    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=0)
    # ... outros campos

    model_config = ConfigDict(frozen=True)

class CreateFarmUseCase:
    """Use Case - Criar fazenda com verificação de permissões e quotas"""

    def __init__(
        self,
        farm_repository: IFarmRepository,
        quota_service: ITenantQuotaService
    ):
        self.farm_repository = farm_repository
        self.quota_service = quota_service

    async def execute(self, command: CreateFarmCommand) -> Farm:
        """
        Cria fazenda.

        Business Rules:
        - TENANT_ADMIN e EDITOR podem criar fazendas
        - VIEWER não pode criar fazendas
        - Respeitando limite do plano (FREE = 1 fazenda)
        """
        # 1. Verificar permissão (VIEWER não pode criar)
        if command.user_role == UserRole.VIEWER:
            raise PermissionDeniedError("VIEWER role cannot create farms")

        # 2. Verificar quota do plano
        can_create, limit = await self.quota_service.can_create_farm(
            command.tenant_id
        )

        if not can_create:
            raise QuotaExceededError(
                f"Farm limit reached ({limit} farms). Upgrade plan to create more."
            )

        # 3. Criar fazenda (com ownership)
        farm = Farm(
            tenant_id=command.tenant_id,
            created_by_user_id=command.user_id,  # ← Ownership
            name=command.name,
            area_hectares=command.area_hectares
        )

        # 4. Salvar
        saved_farm = await self.farm_repository.save(farm)

        return saved_farm
```

### Use Case: Editar Fazenda (Com Verificação de Ownership)

**Arquivo**: `services/api/app/application/use_cases/farms/update_farm.py`

```python
# services/api/app/application/use_cases/farms/update_farm.py

from pydantic import BaseModel, ConfigDict
from uuid import UUID

from app.domain.entities.farm import Farm
from app.domain.entities.user import UserRole
from app.domain.repositories.farm_repository import IFarmRepository
from app.application.exceptions import FarmNotFoundError, PermissionDeniedError

class UpdateFarmCommand(BaseModel):
    """Command para editar fazenda"""
    farm_id: UUID
    tenant_id: UUID
    user_id: UUID
    user_role: UserRole

    name: str | None = None
    area_hectares: float | None = None
    # ... outros campos

    model_config = ConfigDict(frozen=True)

class UpdateFarmUseCase:
    """Use Case - Editar fazenda com verificação de ownership"""

    def __init__(self, farm_repository: IFarmRepository):
        self.farm_repository = farm_repository

    async def execute(self, command: UpdateFarmCommand) -> Farm:
        """
        Edita fazenda.

        Business Rules:
        - SYSTEM_ADMIN: pode editar qualquer fazenda
        - TENANT_ADMIN: pode editar qualquer fazenda do tenant
        - EDITOR: pode editar apenas fazendas que ELE criou
        - VIEWER: não pode editar nenhuma fazenda
        """
        # 1. Buscar fazenda
        farm = await self.farm_repository.find_by_id(
            command.farm_id,
            command.tenant_id
        )

        if not farm:
            raise FarmNotFoundError(f"Farm {command.farm_id} not found")

        # 2. Verificar permissão (usando método do domain)
        if not farm.can_edit(command.user_id, command.user_role):
            raise PermissionDeniedError(
                "You don't have permission to edit this farm. "
                "Only the creator or TENANT_ADMIN can edit."
            )

        # 3. Atualizar campos
        if command.name:
            farm.name = command.name

        if command.area_hectares:
            farm.area_hectares = command.area_hectares

        # 4. Salvar
        updated_farm = await self.farm_repository.save(farm)

        return updated_farm
```

---

## Implementação - Presentation Layer

### Guards de Permissão

**Arquivo**: `services/api/app/presentation/dependencies.py`

```python
# services/api/app/presentation/dependencies.py

from fastapi import HTTPException, status, Depends
from app.domain.entities.user import User, UserRole
from app.presentation.auth import get_current_user

async def require_tenant_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Guard: Requer TENANT_ADMIN ou superior.

    Usar em:
    - Convidar usuários
    - Gerenciar billing
    - Configurações do tenant
    """
    allowed_roles = {UserRole.SYSTEM_ADMIN, UserRole.TENANT_ADMIN}

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires TENANT_ADMIN role"
        )

    return current_user


async def require_editor(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Guard: Requer EDITOR ou superior (não permite VIEWER).

    Usar em:
    - Criar fazenda
    - Criar alerta
    """
    allowed_roles = {
        UserRole.SYSTEM_ADMIN,
        UserRole.TENANT_ADMIN,
        UserRole.EDITOR
    }

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires EDITOR role or higher. VIEWER role has read-only access."
        )

    return current_user


async def require_authenticated(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Guard: Requer apenas autenticação (qualquer role).

    Usar em:
    - Ver fazendas
    - Ver imagens
    - Ver índices
    """
    # Se chegou aqui, está autenticado (get_current_user já valida JWT)
    return current_user
```

### Rotas com Guards

**Arquivo**: `services/api/app/presentation/routers/farms_router.py`

```python
# services/api/app/presentation/routers/farms_router.py

from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.presentation.dependencies import (
    require_editor,
    require_authenticated,
    get_create_farm_use_case,
    get_update_farm_use_case,
    get_list_farms_use_case
)
from app.domain.entities.user import User
from app.presentation.dtos.farm_dtos import (
    CreateFarmRequestDTO,
    UpdateFarmRequestDTO,
    FarmResponseDTO
)

router = APIRouter(prefix="/farms", tags=["farms"])


@router.post(
    "/",
    response_model=FarmResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create farm"
)
async def create_farm(
    request: CreateFarmRequestDTO,
    current_user: Annotated[User, Depends(require_editor)],  # ← EDITOR ou superior
    use_case: Annotated[CreateFarmUseCase, Depends(get_create_farm_use_case)]
):
    """
    Create new farm.

    **Permissions**:
    - ✅ TENANT_ADMIN: Can create (within plan limits)
    - ✅ EDITOR: Can create (within plan limits)
    - ❌ VIEWER: Cannot create (read-only)
    """
    command = CreateFarmCommand(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,  # ← Ownership
        user_role=current_user.role,
        name=request.name,
        area_hectares=request.area_hectares
    )

    farm = await use_case.execute(command)

    return FarmResponseDTO.from_domain(farm)


@router.put(
    "/{farm_id}",
    response_model=FarmResponseDTO,
    summary="Update farm"
)
async def update_farm(
    farm_id: UUID,
    request: UpdateFarmRequestDTO,
    current_user: Annotated[User, Depends(require_editor)],  # ← EDITOR ou superior
    use_case: Annotated[UpdateFarmUseCase, Depends(get_update_farm_use_case)]
):
    """
    Update farm.

    **Permissions**:
    - ✅ TENANT_ADMIN: Can edit ANY farm in tenant
    - ✅ EDITOR: Can edit ONLY farms they created
    - ❌ VIEWER: Cannot edit

    **Note**: Even if EDITOR role, will fail if they didn't create this farm.
    """
    command = UpdateFarmCommand(
        farm_id=farm_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        user_role=current_user.role,  # ← Use case verifica ownership
        name=request.name,
        area_hectares=request.area_hectares
    )

    farm = await use_case.execute(command)

    return FarmResponseDTO.from_domain(farm)


@router.get(
    "/",
    response_model=list[FarmResponseDTO],
    summary="List farms"
)
async def list_farms(
    current_user: Annotated[User, Depends(require_authenticated)],  # ← Qualquer role autenticada
    use_case: Annotated[ListFarmsUseCase, Depends(get_list_farms_use_case)]
):
    """
    List all farms in tenant.

    **Permissions**:
    - ✅ ALL ROLES: Can view farms (read-only for VIEWER)

    **Note**: Returns all farms in tenant, but UI should disable edit buttons for:
    - VIEWER: all farms
    - EDITOR: farms created by others
    """
    farms = await use_case.execute(current_user.tenant_id)

    return [FarmResponseDTO.from_domain(farm) for farm in farms]
```

---

## Fluxo de Convite com Escolha de Role

### Use Case: Convidar Usuário

**Arquivo**: `services/api/app/application/use_cases/users/invite_user.py`

```python
# services/api/app/application/use_cases/users/invite_user.py

from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
import secrets

from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.application.exceptions import DuplicateEmailError, PermissionDeniedError

class InviteUserCommand(BaseModel):
    """Command para convidar usuário"""
    tenant_id: UUID
    inviter_user_id: UUID
    inviter_role: UserRole

    email: EmailStr
    full_name: str
    invited_role: UserRole  # ← Role escolhido pelo TENANT_ADMIN (EDITOR ou VIEWER)

    model_config = ConfigDict(frozen=True)

class InviteUserUseCase:
    """Use Case - Convidar usuário com role customizado"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self, command: InviteUserCommand) -> User:
        """
        Envia convite para novo usuário.

        Business Rules:
        - Apenas TENANT_ADMIN pode convidar
        - Email verificado obrigatório
        - Pode convidar como EDITOR ou VIEWER
        - Não pode convidar como TENANT_ADMIN (apenas 1 por tenant)
        """
        # 1. Verificar permissão
        if command.inviter_role != UserRole.TENANT_ADMIN:
            raise PermissionDeniedError("Only TENANT_ADMIN can invite users")

        # 2. Validar role convidado (não pode convidar TENANT_ADMIN ou SYSTEM_ADMIN)
        if command.invited_role in {UserRole.TENANT_ADMIN, UserRole.SYSTEM_ADMIN}:
            raise PermissionDeniedError(
                "Cannot invite user as TENANT_ADMIN or SYSTEM_ADMIN. "
                "Choose EDITOR (can create/edit own farms) or VIEWER (read-only)."
            )

        # 3. Verificar se email já existe
        existing_user = await self.user_repository.find_by_email(command.email)
        if existing_user:
            raise DuplicateEmailError(f"Email {command.email} already registered")

        # 4. Criar usuário com role escolhido
        user = User(
            tenant_id=command.tenant_id,
            email=command.email,
            password_hash="",  # Vai definir no primeiro login
            full_name=command.full_name,
            role=command.invited_role,  # ← EDITOR ou VIEWER
            is_active=False,  # Ativa após aceitar convite
            email_verification_token=secrets.token_urlsafe(32)
        )

        saved_user = await self.user_repository.save(user)

        # TODO: Enviar email de convite com link para definir senha

        return saved_user
```

### Rota de Convite

**Arquivo**: `services/api/app/presentation/routers/users_router.py`

```python
# services/api/app/presentation/routers/users_router.py

from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.presentation.dependencies import require_tenant_admin, require_verified_email
from app.domain.entities.user import User, UserRole

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/invite",
    status_code=status.HTTP_201_CREATED,
    summary="Invite user to tenant"
)
async def invite_user(
    request: InviteUserRequestDTO,
    current_user: Annotated[
        User,
        Depends(require_tenant_admin),  # ← Apenas TENANT_ADMIN
        Depends(require_verified_email)  # ← Email verificado obrigatório
    ],
    use_case: Annotated[InviteUserUseCase, Depends(get_invite_user_use_case)]
):
    """
    Invite user to tenant with custom role.

    **Permissions**:
    - ✅ TENANT_ADMIN only (with verified email)
    - ❌ EDITOR, VIEWER: Cannot invite

    **Role Options**:
    - `editor`: Can create/edit own farms (collaborative)
    - `viewer`: Can only view data (read-only)

    **Cannot invite as**:
    - `tenant_admin`: Only one per tenant (the owner)
    - `system_admin`: Reserved for VivaCampo team
    """
    command = InviteUserCommand(
        tenant_id=current_user.tenant_id,
        inviter_user_id=current_user.id,
        inviter_role=current_user.role,
        email=request.email,
        full_name=request.full_name,
        invited_role=request.role  # ← EDITOR ou VIEWER
    )

    user = await use_case.execute(command)

    return {"message": f"Invitation sent to {request.email}"}
```

### Request DTO

**Arquivo**: `services/api/app/presentation/dtos/user_dtos.py`

```python
# services/api/app/presentation/dtos/user_dtos.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.domain.entities.user import UserRole

class InviteUserRequestDTO(BaseModel):
    """Request DTO - Convidar usuário"""
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole  # ← EDITOR ou VIEWER

    model_config = ConfigDict(frozen=True)

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: UserRole) -> UserRole:
        """Apenas EDITOR ou VIEWER permitidos"""
        allowed_roles = {UserRole.EDITOR, UserRole.VIEWER}

        if v not in allowed_roles:
            raise ValueError(
                "Invalid role. Choose 'editor' (can create/edit own farms) "
                "or 'viewer' (read-only access)."
            )

        return v
```

---

## Frontend - UI de Convite

### Componente: Invite User Modal

**Arquivo**: `services/app-ui/src/components/settings/InviteUserModal.tsx`

```tsx
// services/app-ui/src/components/settings/InviteUserModal.tsx

'use client';

import { useState } from 'react';

type UserRole = 'editor' | 'viewer';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function InviteUserModal({ isOpen, onClose }: Props) {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<UserRole>('editor');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/users/invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ email, full_name: fullName, role })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to send invitation');
      }

      // Sucesso
      onClose();
      // TODO: Mostrar toast de sucesso

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao enviar convite');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-6">
          Convidar Usuário
        </h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg"
              placeholder="usuario@email.com"
            />
          </div>

          {/* Nome */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Nome Completo
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg"
              placeholder="João Silva"
            />
          </div>

          {/* Role (Customizável) */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Nível de Acesso
            </label>

            {/* Opção A: VIEWER (Somente Leitura) */}
            <label className="flex items-start p-4 border-2 border-gray-200 rounded-lg mb-3 cursor-pointer hover:border-green-600 transition-colors">
              <input
                type="radio"
                name="role"
                value="viewer"
                checked={role === 'viewer'}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="mt-1 text-green-600 focus:ring-green-600"
              />
              <div className="ml-3">
                <div className="font-semibold text-slate-900">
                  👀 Visualizador (Viewer)
                </div>
                <p className="text-sm text-slate-600 mt-1">
                  Pode apenas <strong>visualizar</strong> fazendas, imagens e alertas.
                  Não pode criar ou editar nada.
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  ✅ Ver fazendas • ✅ Ver imagens • ✅ Ver alertas • ❌ Criar/editar
                </p>
              </div>
            </label>

            {/* Opção B: EDITOR (Colaborativo) */}
            <label className="flex items-start p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-green-600 transition-colors">
              <input
                type="radio"
                name="role"
                value="editor"
                checked={role === 'editor'}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="mt-1 text-green-600 focus:ring-green-600"
              />
              <div className="ml-3">
                <div className="font-semibold text-slate-900">
                  ✏️ Editor (Editor)
                </div>
                <p className="text-sm text-slate-600 mt-1">
                  Pode <strong>criar e editar</strong> fazendas que ele próprio criou.
                  Pode ver fazendas de outros (somente leitura).
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  ✅ Criar fazendas • ✅ Editar próprias • ✅ Ver todas • ❌ Editar de outros
                </p>
              </div>
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Botões */}
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-slate-100 text-slate-900 rounded-lg hover:bg-slate-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Enviando...' : 'Enviar Convite'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

---

## Checklist de Implementação

### Domain Layer
- [ ] Atualizar `UserRole` enum com EDITOR e VIEWER
- [ ] Adicionar campo `created_by_user_id` em Farm entity
- [ ] Adicionar método `can_edit()` em Farm entity
- [ ] Validações de permissão no domain (business rules)

### Application Layer
- [ ] CreateFarmUseCase verifica role (VIEWER não pode criar)
- [ ] UpdateFarmUseCase verifica ownership (EDITOR só edita próprias)
- [ ] DeleteFarmUseCase verifica ownership
- [ ] InviteUserUseCase permite escolha entre EDITOR/VIEWER
- [ ] ListFarmsUseCase retorna todas (frontend decide botões)

### Infrastructure Layer
- [ ] Adicionar coluna `created_by_user_id` na tabela farms
- [ ] Migration para adicionar coluna
- [ ] FarmRepository salva `created_by_user_id`

### Presentation Layer
- [ ] Guard `require_tenant_admin` (convidar, billing)
- [ ] Guard `require_editor` (criar/editar fazendas)
- [ ] Guard `require_authenticated` (visualização)
- [ ] Rotas de farms usam guards corretos
- [ ] Rota `/users/invite` com validação de role

### Frontend
- [ ] InviteUserModal com escolha de role (EDITOR/VIEWER)
- [ ] Dashboard mostra role do usuário atual
- [ ] Botões de editar desabilitados para VIEWER
- [ ] Botões de editar desabilitados para EDITOR (em fazendas de outros)
- [ ] Badge visual mostrando "Criado por você" vs "Criado por Fulano"

### Testes
- [ ] Teste: VIEWER não pode criar fazenda (403)
- [ ] Teste: EDITOR pode criar fazenda (201)
- [ ] Teste: EDITOR pode editar fazenda própria (200)
- [ ] Teste: EDITOR não pode editar fazenda de outro (403)
- [ ] Teste: TENANT_ADMIN pode editar qualquer fazenda (200)
- [ ] Teste: Convite com role inválido (400)
- [ ] Teste: Multi-tenant isolation (EDITOR não vê fazendas de outro tenant)

---

## Casos de Uso Reais

### Caso 1: Consultoria Agrícola
```
TENANT: "AgroConsult Ltda"

TENANT_ADMIN: João (consultor principal)
  - Cria fazendas dos clientes
  - Convida consultores juniores como EDITOR
  - Convida clientes como VIEWER

EDITOR: Maria (consultora junior)
  - Cria fazendas dos clientes dela
  - Edita apenas fazendas que ela criou
  - Vê fazendas de João (somente leitura)

VIEWER: Fazendeiro Pedro (cliente)
  - Vê fazendas dele (criadas por João)
  - Vê imagens, índices, alertas
  - Não pode editar nada
```

### Caso 2: Cooperativa
```
TENANT: "Cooperativa Vale Verde"

TENANT_ADMIN: Diretor da Cooperativa
  - Gerencia billing
  - Convida todos agricultores como EDITOR

EDITOR: Agricultores cooperados
  - Cada um cria suas próprias fazendas
  - Edita apenas suas fazendas
  - Vê fazendas de outros cooperados (benchmarking)
```

### Caso 3: Fazenda Familiar
```
TENANT: "Fazenda Dois Irmãos"

TENANT_ADMIN: Proprietário
  - Cria fazendas
  - Convida filho como EDITOR
  - Convida contador como VIEWER

EDITOR: Filho (gestor operacional)
  - Cria talhões novos
  - Edita apenas o que criou

VIEWER: Contador
  - Acessa relatórios
  - Não pode modificar nada
```

---

## Migração de Dados

Se já existem fazendas sem `created_by_user_id`:

```sql
-- Migration: Atribuir fazendas existentes ao TENANT_ADMIN

UPDATE farms
SET created_by_user_id = (
    SELECT id
    FROM users
    WHERE users.tenant_id = farms.tenant_id
      AND users.role = 'tenant_admin'
    LIMIT 1
)
WHERE created_by_user_id IS NULL;
```

---

## Resumo

✅ **TENANT_ADMIN**: Pode tudo (owner)
✅ **EDITOR**: Cria e edita próprias fazendas, vê todas (colaborativo)
✅ **VIEWER**: Somente leitura (consulta, auditoria)
✅ **Customizável**: TENANT_ADMIN escolhe role ao convidar
✅ **Ownership**: Farm rastreia quem criou (`created_by_user_id`)
✅ **Guards**: Validação de permissões em cada camada

Quer que eu comece implementando alguma parte específica agora? 🚀
