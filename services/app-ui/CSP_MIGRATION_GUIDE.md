# Guia de Migração para CSP Mais Restritivo

## Status Atual

A Content Security Policy (CSP) atual usa `unsafe-inline` e `unsafe-eval`, o que reduz a segurança contra ataques XSS.

**CSP Atual (middleware.ts:45-53):**
```javascript
const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-eval' 'unsafe-inline'",  // ⚠️ Inseguro
    "style-src 'self' 'unsafe-inline' https://unpkg.com", // ⚠️ Inseguro
    "img-src 'self' data: https: blob:",
    "font-src 'self' data:",
    "connect-src 'self' http://localhost:8000 https://unpkg.com",
    "frame-ancestors 'none'"
].join('; ')
```

## Por que `unsafe-inline` e `unsafe-eval` são Perigosos?

### `unsafe-inline`
- Permite execução de scripts inline (`<script>alert('xss')</script>`)
- Permite estilos inline (`<div style="...">`)
- Abre brecha para XSS attacks

### `unsafe-eval`
- Permite `eval()`, `new Function()`, `setTimeout(string)`
- Usado por Next.js no modo desenvolvimento
- Pode executar código malicioso injetado

## Abordagens para Remover `unsafe-*`

### Opção 1: Usar Nonces (Recomendado para Next.js)

Nonces são tokens únicos gerados por request que permitem apenas scripts específicos.

**Implementação:**

1. Atualizar `middleware.ts`:

```typescript
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import crypto from 'crypto'

export function middleware(request: NextRequest) {
    // Gerar nonce único
    const nonce = crypto.randomBytes(16).toString('base64')

    const response = NextResponse.next()

    // CSP com nonce
    const csp = [
        "default-src 'self'",
        `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
        `style-src 'self' 'nonce-${nonce}' https://unpkg.com`,
        "img-src 'self' data: https: blob:",
        "font-src 'self' data:",
        "connect-src 'self' http://localhost:8000 https://unpkg.com",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'"
    ].join('; ')

    response.headers.set('Content-Security-Policy', csp)

    // Passar nonce para o app via header
    response.headers.set('x-nonce', nonce)

    return response
}
```

2. Criar hook para acessar o nonce:

```typescript
// src/lib/useNonce.ts
import { headers } from 'next/headers'

export function useNonce() {
    const headersList = headers()
    return headersList.get('x-nonce') || ''
}
```

3. Usar nonce em scripts inline:

```tsx
import { useNonce } from '@/lib/useNonce'

export default function MyPage() {
    const nonce = useNonce()

    return (
        <>
            <script nonce={nonce}>
                {`console.log('This script is allowed')`}
            </script>
        </>
    )
}
```

### Opção 2: Usar Hashes para Scripts Estáticos

Para scripts que não mudam, use hashes SHA-256.

**Exemplo:**

```javascript
// Script
const scriptContent = "console.log('Hello')"

// Gerar hash
const hash = crypto.createHash('sha256')
    .update(scriptContent)
    .digest('base64')

// Usar no CSP
"script-src 'self' 'sha256-{hash}'"
```

### Opção 3: Mover Scripts Inline para Arquivos Externos

Melhor prática: sem scripts inline.

**Antes:**
```tsx
<script>{`alert('hello')`}</script>
```

**Depois:**
```tsx
// public/scripts/hello.js
alert('hello')

// Componente
<Script src="/scripts/hello.js" />
```

## CSP Recomendado para Produção

```javascript
const csp = [
    // Default
    "default-src 'self'",

    // Scripts: apenas self e nonces
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,

    // Styles: self, nonces e CDNs confiáveis
    `style-src 'self' 'nonce-${nonce}' https://unpkg.com`,

    // Images: self, data URIs, HTTPS, blobs
    "img-src 'self' data: https: blob:",

    // Fonts: self e data URIs
    "font-src 'self' data:",

    // API connections: backend e CDNs
    "connect-src 'self' https://api.vivacampo.com https://unpkg.com",

    // Frames: nenhum
    "frame-ancestors 'none'",

    // Base URI: apenas self
    "base-uri 'self'",

    // Forms: apenas self
    "form-action 'self'",

    // Upgrade insecure requests
    "upgrade-insecure-requests"
].join('; ')
```

## Problema com Next.js Development

Next.js usa `eval()` no modo desenvolvimento, o que requer `unsafe-eval`.

**Solução:** CSP diferente por ambiente.

```typescript
const isDevelopment = process.env.NODE_ENV === 'development'

const csp = [
    "default-src 'self'",
    isDevelopment
        ? "script-src 'self' 'unsafe-eval' 'unsafe-inline'" // Dev
        : `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`, // Prod
    // ...
].join('; ')
```

## Problema com Leaflet (Mapa)

Leaflet carrega CSS via `<link>` dinâmico, o que pode violar CSP.

**Solução 1:** Carregar CSS estaticamente

```tsx
// Em layout.tsx ou _document.tsx
import 'leaflet/dist/leaflet.css'
```

**Solução 2:** Permitir unpkg.com no CSP

```javascript
"style-src 'self' https://unpkg.com"
```

## Passos de Migração

### Fase 1: Desenvolvimento (Atual)

```javascript
// Permitir unsafe-* apenas em dev
const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline' https://unpkg.com",
    // ...
]
```

✅ **Status:** Implementado

### Fase 2: Report-Only Mode

Testar CSP restritivo sem bloquear:

```typescript
// Use Content-Security-Policy-Report-Only
response.headers.set('Content-Security-Policy-Report-Only', strictCsp)

// Configure report URI
const strictCsp = [
    // ... CSP restritivo
    "report-uri /api/csp-report"
].join('; ')
```

Criar endpoint para receber reports:

```typescript
// src/app/api/csp-report/route.ts
export async function POST(request: Request) {
    const report = await request.json()
    console.log('CSP Violation:', report)
    // Log to monitoring service
    return new Response('OK', { status: 200 })
}
```

⏳ **Próximo Passo**

### Fase 3: Implementar Nonces

1. Gerar nonces no middleware
2. Passar para componentes
3. Adicionar nonce a scripts necessários
4. Testar em staging

⏳ **Após testes**

### Fase 4: Produção Restritivo

Ativar CSP restritivo em produção:

```javascript
const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'self' 'nonce-${nonce}'`,
    // ...
]
```

✅ **Objetivo final**

## Testes

### Verificar CSP no Browser

1. Abrir DevTools
2. Console > Filter: "CSP"
3. Procurar violações

### Ferramentas

- [CSP Evaluator](https://csp-evaluator.withgoogle.com/) - Avaliar sua CSP
- [Report URI](https://report-uri.com/) - Monitoring de CSP

## Recursos

- [MDN: Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [Next.js CSP](https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy)

## Conclusão

A migração para CSP restritivo é um processo gradual:

1. ✅ **Atual:** CSP permissivo (desenvolvimento)
2. ⏳ **Próximo:** Report-only mode (teste)
3. ⏳ **Depois:** Nonces (staging)
4. ⏳ **Final:** CSP restritivo (produção)

**Tempo estimado:** 2-4 semanas

**Benefício:** Proteção significativa contra XSS attacks
