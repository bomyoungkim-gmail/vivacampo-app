# Guia de Migração para Autenticação OIDC Real

Este guia detalha os passos necessários para migrar da autenticação mock (desenvolvimento) para um sistema de autenticação OIDC real e seguro em produção.

---

## 📋 Pré-requisitos

- [ ] Escolher um provedor OIDC (veja opções abaixo)
- [ ] Ter acesso ao backend da aplicação (FastAPI)
- [ ] Entender os fluxos OAuth 2.0 / OIDC
- [ ] Tempo estimado: 4-8 horas

---

## 🔐 Opções de Provedores OIDC

### 1. **Auth0** (Recomendado para início rápido)

**Prós:**
- Setup rápido (< 30 minutos)
- Free tier generoso (7,000 usuários ativos)
- SDKs oficiais para Next.js
- Suporte a Social Login (Google, Facebook, etc.)
- Dashboard intuitivo

**Contras:**
- Vendor lock-in
- Custos podem crescer com escala

**Guia:** https://auth0.com/docs/quickstart/webapp/nextjs

---

### 2. **Azure AD (Microsoft Entra ID)**

**Prós:**
- Integração nativa com Microsoft 365
- Excelente para empresas
- Suporte enterprise
- MFA nativo

**Contras:**
- Interface complexa
- Mais caro
- Curva de aprendizado

**Guia:** https://learn.microsoft.com/en-us/azure/active-directory/develop/

---

### 3. **Google Cloud Identity Platform**

**Prós:**
- Integração com Google Workspace
- Boa documentação
- Free tier
- Firebase Authentication

**Contras:**
- Limitado a Google ecosystem
- Menos features enterprise

**Guia:** https://cloud.google.com/identity-platform/docs

---

### 4. **Keycloak** (Open Source, Self-Hosted)

**Prós:**
- Open source e gratuito
- Controle total
- Sem vendor lock-in
- Features enterprise completas

**Contras:**
- Requer infraestrutura própria
- Manutenção manual
- Setup mais complexo

**Guia:** https://www.keycloak.org/getting-started/getting-started-docker

---

### 5. **AWS Cognito**

**Prós:**
- Integração com AWS
- Escalável
- Preço por uso
- MFA e segurança robustos

**Contras:**
- UI limitado
- Complexidade AWS
- Custos variáveis

**Guia:** https://docs.aws.amazon.com/cognito/

---

## 🚀 Passo a Passo - Implementação com Auth0

Vamos usar Auth0 como exemplo por ser o mais rápido de implementar.

### Passo 1: Criar Conta no Auth0

1. Acesse https://auth0.com/signup
2. Crie uma conta gratuita
3. Crie um novo "Tenant" (ex: vivacampo-dev)

### Passo 2: Configurar Application no Auth0

1. No dashboard, vá em **Applications** > **Create Application**
2. Nome: "VivaCampo App UI"
3. Tipo: **Regular Web Application**
4. Tecnologia: **Next.js**

5. Configure as URLs:
   - **Allowed Callback URLs**:
     ```
     http://localhost:3002/app/api/auth/callback
     https://app.vivacampo.com/app/api/auth/callback
     ```
   - **Allowed Logout URLs**:
     ```
     http://localhost:3002/app
     https://app.vivacampo.com/app
     ```
   - **Allowed Web Origins**:
     ```
     http://localhost:3002
     https://app.vivacampo.com
     ```

6. Salve as credenciais:
   - **Domain**: `vivacampo-dev.us.auth0.com`
   - **Client ID**: `abc123...`
   - **Client Secret**: `xyz789...` (MANTER SECRETO!)

### Passo 3: Instalar Dependências

```bash
cd services/app-ui
npm install @auth0/nextjs-auth0
```

### Passo 4: Configurar Variáveis de Ambiente

Criar/atualizar `.env.local`:

```bash
# Auth0 Configuration
AUTH0_SECRET='use [openssl rand -hex 32] para gerar'
AUTH0_BASE_URL='http://localhost:3002/app'
AUTH0_ISSUER_BASE_URL='https://vivacampo-dev.us.auth0.com'
AUTH0_CLIENT_ID='seu_client_id_aqui'
AUTH0_CLIENT_SECRET='seu_client_secret_aqui'

# Disable mock auth
NEXT_PUBLIC_ENABLE_MOCK_AUTH=false
```

**Produção (`.env.production`):**
```bash
AUTH0_SECRET='gerar-novo-secret-para-producao'
AUTH0_BASE_URL='https://app.vivacampo.com/app'
AUTH0_ISSUER_BASE_URL='https://vivacampo.us.auth0.com'
AUTH0_CLIENT_ID='seu_client_id_producao'
AUTH0_CLIENT_SECRET='seu_client_secret_producao'
NEXT_PUBLIC_ENABLE_MOCK_AUTH=false
```

### Passo 5: Criar API Route Handler

Criar `src/app/api/auth/[auth0]/route.ts`:

```typescript
import { handleAuth } from '@auth0/nextjs-auth0'

export const GET = handleAuth()
```

### Passo 6: Atualizar Login Page

Substituir `src/app/login/page.tsx`:

```typescript
'use client'

import { useUser } from '@auth0/nextjs-auth0/client'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function LoginPage() {
    const { user, error, isLoading } = useUser()
    const router = useRouter()

    useEffect(() => {
        // Se já está autenticado, redirecionar
        if (user) {
            router.push('/dashboard')
        }
    }, [user, router])

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
                    <p className="mt-2 text-gray-600">Carregando...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="rounded-lg bg-red-50 p-6 text-center">
                    <h2 className="text-lg font-semibold text-red-900">Erro de Autenticação</h2>
                    <p className="mt-2 text-red-700">{error.message}</p>
                </div>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
            <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-8 shadow-lg">
                <div className="text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-blue-600">
                        <svg className="h-10 w-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="mt-6 text-3xl font-bold text-gray-900">VivaCampo</h2>
                    <p className="mt-2 text-sm text-gray-600">
                        Sistema de Monitoramento Agrícola
                    </p>
                </div>

                <div className="mt-8">
                    <a
                        href="/app/api/auth/login"
                        className="flex w-full justify-center rounded-md bg-gradient-to-r from-green-600 to-blue-600 px-4 py-3 text-sm font-medium text-white shadow-sm hover:from-green-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    >
                        Entrar com Auth0
                    </a>
                </div>

                <div className="mt-4 text-center text-xs text-gray-500">
                    Autenticação segura via Auth0
                </div>
            </div>
        </div>
    )
}
```

### Passo 7: Atualizar Auth Helper

Modificar `src/lib/auth.ts`:

```typescript
import { useUser } from '@auth0/nextjs-auth0/client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export interface User {
    id: string
    email: string
    name: string
    picture?: string
}

/**
 * Custom hook for authentication protection using Auth0
 */
export function useAuthProtection() {
    const { user, error, isLoading } = useUser()
    const router = useRouter()

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/login')
        }
    }, [user, isLoading, router])

    return {
        isAuthenticated: !!user,
        isLoading,
        user: user as User | null,
        error,
    }
}

/**
 * Logout function using Auth0
 */
export function logout() {
    window.location.href = '/app/api/auth/logout'
}

// Remover funções relacionadas a localStorage
// getAuthToken(), getCurrentUser(), setAuthData()
```

### Passo 8: Atualizar API Client

Modificar `src/lib/api.ts` para usar token do Auth0:

```typescript
import axios from 'axios'
import { APP_CONFIG } from './config'

const api = axios.create({
    baseURL: APP_CONFIG.API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Add auth token from Auth0
api.interceptors.request.use(async (config) => {
    // Buscar token do Auth0
    const response = await fetch('/app/api/auth/token')
    if (response.ok) {
        const { accessToken } = await response.json()
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`
        }
    }
    return config
})

// Handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            window.location.href = `${APP_CONFIG.BASE_PATH}/api/auth/login`
        }
        return Promise.reject(error)
    }
)

export default api
// ... resto do código
```

### Passo 9: Criar Token API Route

Criar `src/app/api/auth/token/route.ts`:

```typescript
import { getAccessToken } from '@auth0/nextjs-auth0'
import { NextResponse } from 'next/server'

export async function GET() {
    try {
        const { accessToken } = await getAccessToken()
        return NextResponse.json({ accessToken })
    } catch (error) {
        return NextResponse.json({ accessToken: null }, { status: 401 })
    }
}
```

### Passo 10: Atualizar Backend (FastAPI)

No backend, atualizar para validar tokens Auth0:

```python
# services/api/app/core/auth.py
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

AUTH0_DOMAIN = "vivacampo-dev.us.auth0.com"
AUTH0_AUDIENCE = "https://api.vivacampo.com"  # Configurar no Auth0
ALGORITHMS = ["RS256"]

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials

    # Buscar JWKS do Auth0
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        jwks = await client.get(jwks_url)
        keys = jwks.json()

    try:
        # Validar token
        payload = jwt.decode(
            token,
            keys,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Passo 11: Remover Código Mock

**IMPORTANTE:** Deletar ou comentar:

- ❌ `generateMockToken()` em `login/page.tsx`
- ❌ Código de mock OIDC no backend
- ❌ Referências a localStorage para tokens

### Passo 12: Testar Fluxo Completo

1. **Desenvolvimento:**
   ```bash
   npm run dev
   # Acessar http://localhost:3002/app
   # Deve redirecionar para Auth0
   # Após login, deve voltar para /app/dashboard
   ```

2. **Verificar:**
   - [ ] Login funciona
   - [ ] Token válido é enviado nas requisições
   - [ ] Logout funciona
   - [ ] Refresh automático de token
   - [ ] Redirecionamento após login
   - [ ] Proteção de rotas funciona

3. **Produção:**
   ```bash
   # Atualizar variáveis no servidor
   # Deploy
   # Testar em https://app.vivacampo.com/app
   ```

---

## 🔒 Checklist de Segurança Pós-Migração

- [ ] Mock auth desabilitado (`NEXT_PUBLIC_ENABLE_MOCK_AUTH=false`)
- [ ] Tokens armazenados em cookies HttpOnly (Auth0 cuida disso)
- [ ] HTTPS em produção
- [ ] Secrets não commitados no git
- [ ] CORS configurado corretamente
- [ ] Rate limiting ativo
- [ ] MFA habilitado no Auth0
- [ ] Logs de auditoria ativados
- [ ] Tokens com expiração curta (15-60 min)
- [ ] Refresh tokens implementados

---

## 🐛 Troubleshooting

### Erro: "Callback URL mismatch"
- Verifique se a URL está exatamente igual no Auth0 e na aplicação
- Inclua porta se for localhost (`:3002`)

### Erro: "Invalid state"
- Limpe cookies do navegador
- Verifique `AUTH0_SECRET` (deve ser o mesmo em todos os servidores)

### Token não chega no backend
- Verifique interceptor do axios
- Confirme que `/api/auth/token` está retornando token
- Veja console do navegador para erros

### Loop de redirecionamento
- Verifique `AUTH0_BASE_URL` (deve incluir `/app` se usar basePath)
- Confirme callback URL no Auth0

---

## 📚 Recursos Adicionais

- [Auth0 Next.js SDK](https://github.com/auth0/nextjs-auth0)
- [OIDC Specification](https://openid.net/connect/)
- [OAuth 2.0 Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## ✅ Conclusão

Após seguir este guia:

✅ Autenticação real e segura implementada
✅ Mock auth completamente removido
✅ Tokens gerenciados por provedor confiável
✅ MFA e features enterprise disponíveis
✅ Aplicação pronta para produção

**Tempo estimado:** 4-8 horas (primeira vez)
**Dificuldade:** Intermediária
**Segurança:** Alta ✓
