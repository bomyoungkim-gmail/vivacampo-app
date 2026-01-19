# Documentação de Segurança - VivaCampo App UI

## 🚨 Avisos Críticos de Segurança

### 1. Autenticação Mock (DESENVOLVIMENTO APENAS)

**Status:** ⚠️ **NÃO SEGURO PARA PRODUÇÃO**

O arquivo `src/app/login/page.tsx` contém uma função `generateMockToken()` que gera tokens JWT falsos para desenvolvimento.

**Problemas:**
- Qualquer email pode fazer login
- Assinatura fake: `'mock-signature'`
- Sem validação de senha
- Sem rate limiting

**Solução para Produção:**
```typescript
// REMOVER: generateMockToken()
// IMPLEMENTAR: Real OIDC provider

// Opções recomendadas:
// 1. Google OAuth 2.0
// 2. Azure AD (Microsoft Entra ID)
// 3. Auth0
// 4. AWS Cognito
// 5. Keycloak (self-hosted)
```

### 2. Armazenamento de Tokens em localStorage

**Status:** ⚠️ **VULNERÁVEL A XSS**

Atualmente os tokens são armazenados em `localStorage`, que é acessível via JavaScript.

**Riscos:**
- Qualquer XSS vulnerability compromete a sessão
- Tokens expostos via DevTools
- Sem proteção HttpOnly

**Solução Recomendada:**
```typescript
// Migrar para cookies HttpOnly + Secure + SameSite
// No backend (FastAPI):
response.set_cookie(
    key="auth_token",
    value=token,
    httponly=True,      # Não acessível via JavaScript
    secure=True,        # Apenas HTTPS
    samesite="strict",  # Proteção CSRF
    max_age=3600
)
```

### 3. Headers de Segurança Implementados

✅ **Implementado em:** `next.config.js` e `src/middleware.ts`

Headers configurados:
- `Strict-Transport-Security`: Force HTTPS
- `X-Content-Type-Options`: Previne MIME sniffing
- `X-Frame-Options`: Previne clickjacking
- `X-XSS-Protection`: Proteção XSS básica
- `Referrer-Policy`: Controla informações de referrer
- `Content-Security-Policy`: Controla recursos carregados
- `Permissions-Policy`: Controla APIs do browser

## 🔐 Melhorias de Segurança Implementadas

### Middleware de Autenticação

**Arquivo:** `src/middleware.ts`

Funcionalidades:
- ✅ Proteção automática de rotas autenticadas
- ✅ Redirecionamento para login se não autenticado
- ✅ Headers de segurança em todas as respostas
- ✅ Content Security Policy (CSP)

Rotas protegidas:
- `/app/dashboard`
- `/app/farms`
- `/app/signals`
- `/app/ai-assistant`

### Hook de Autenticação Centralizado

**Arquivo:** `src/lib/auth.ts`

Funções disponíveis:
- `useAuthProtection()`: Hook para proteção de páginas
- `logout()`: Limpa sessão e redireciona
- `getAuthToken()`: Recupera token atual
- `getCurrentUser()`: Recupera dados do usuário
- `setAuthData()`: Armazena token e dados do usuário

**Uso:**
```typescript
import { useAuthProtection, logout } from '@/lib/auth'

export default function MyPage() {
    const { isAuthenticated, isLoading, user } = useAuthProtection()

    if (isLoading) return <Loading />

    return <div>Olá, {user?.email}</div>
}
```

## 📋 Checklist de Segurança para Produção

### Autenticação e Autorização

- [ ] **CRÍTICO:** Remover `generateMockToken()` do código
- [ ] **CRÍTICO:** Implementar OIDC provider real
- [ ] **CRÍTICO:** Migrar tokens para cookies HttpOnly
- [ ] Implementar refresh token rotation
- [ ] Adicionar rate limiting no backend
- [ ] Implementar 2FA (Two-Factor Authentication)
- [ ] Adicionar CSRF token validation
- [ ] Implementar session timeout
- [ ] Adicionar audit logging de autenticação

### Armazenamento de Dados

- [ ] **CRÍTICO:** Não armazenar dados sensíveis em localStorage
- [ ] Criptografar dados sensíveis em trânsito (HTTPS)
- [ ] Validar todos os inputs do usuário
- [ ] Sanitizar dados antes de exibir (prevenir XSS)

### Headers e Configuração

- [x] Headers de segurança configurados
- [x] CSP implementado
- [ ] Ajustar CSP para produção (remover 'unsafe-eval', 'unsafe-inline')
- [ ] Configurar CORS adequadamente
- [ ] Adicionar HSTS preload
- [ ] Configurar certificado SSL/TLS válido

### Monitoramento e Logging

- [ ] Implementar logging de eventos de segurança
- [ ] Configurar alertas para tentativas de login suspeitas
- [ ] Monitorar erros de autenticação
- [ ] Implementar audit trail
- [ ] Configurar SIEM (Security Information and Event Management)

### Testes de Segurança

- [ ] Realizar scan de vulnerabilidades (OWASP ZAP, Burp Suite)
- [ ] Teste de penetração
- [ ] Code review focado em segurança
- [ ] Análise de dependências (npm audit)
- [ ] Teste de XSS
- [ ] Teste de CSRF
- [ ] Teste de SQL Injection (se aplicável)

## 🔧 Configuração Recomendada para Produção

### Variáveis de Ambiente

Criar arquivo `.env.production`:

```bash
# API Configuration
NEXT_PUBLIC_API_BASE=https://api.vivacampo.com

# OIDC Configuration (exemplo com Auth0)
NEXT_PUBLIC_OIDC_ISSUER=https://vivacampo.auth0.com
NEXT_PUBLIC_OIDC_CLIENT_ID=your_client_id
OIDC_CLIENT_SECRET=your_client_secret  # Backend only!

# Session Configuration
SESSION_SECRET=generate-strong-random-secret-here
SESSION_MAX_AGE=3600

# Security
ENABLE_MOCK_AUTH=false  # MUST be false in production!
```

### Content Security Policy para Produção

Atualizar `src/middleware.ts`:

```typescript
// CSP mais restritivo para produção
const csp = [
    "default-src 'self'",
    "script-src 'self'",  // Remover unsafe-eval e unsafe-inline
    "style-src 'self' https://unpkg.com",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' https://api.vivacampo.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'"
].join('; ')
```

## 🛡️ Boas Práticas de Desenvolvimento

### 1. Nunca Commit Secrets

```bash
# Adicionar ao .gitignore
.env.local
.env.production
.env*.local
*.key
*.pem
```

### 2. Validar Todos os Inputs

```typescript
// Usar Zod para validação
import { z } from 'zod'

const loginSchema = z.object({
    email: z.string().email(),
    password: z.string().min(8)
})
```

### 3. Sanitizar Outputs

```typescript
// Evitar dangerouslySetInnerHTML
// Usar text content ao invés de innerHTML
// React já faz escape automático
```

### 4. Princípio do Menor Privilégio

```typescript
// Não expor mais dados do que necessário
// Filtrar dados sensíveis antes de enviar ao frontend
interface PublicUser {
    id: string
    email: string
    name: string
    // Não incluir: password hash, tokens internos, etc.
}
```

## 📞 Reportando Vulnerabilidades

Se você descobrir uma vulnerabilidade de segurança, por favor:

1. **NÃO** crie uma issue pública
2. Envie email para: security@vivacampo.com
3. Inclua:
   - Descrição da vulnerabilidade
   - Passos para reproduzir
   - Impacto potencial
   - Sugestões de correção (se tiver)

## 📚 Recursos Adicionais

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Next.js Security Best Practices](https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## 📝 Histórico de Mudanças

### 2026-01-17 - Melhorias de Segurança Implementadas

- ✅ Criado middleware de autenticação centralizado
- ✅ Implementado hook `useAuthProtection()`
- ✅ Adicionados headers de segurança
- ✅ Removido código de autenticação duplicado
- ✅ Adicionados avisos de segurança no código
- ⚠️ Mock authentication ainda presente (desenvolvimento apenas)

### Próximas Melhorias Planejadas

1. Migração para OIDC real
2. Implementação de refresh tokens
3. Migração para cookies HttpOnly
4. Rate limiting
5. Audit logging
