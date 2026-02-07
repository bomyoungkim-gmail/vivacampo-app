# Plano de Implementação: Landing Page, Autenticação e Multi-Tenant Login

## Visão Geral

Este plano implementa 3 funcionalidades críticas que estão faltando:

1. **Landing Page Profissional** - Página inicial atrativa com design moderno
2. **Autenticação Completa** - Cadastro, login, recuperação de senha
3. **URLs de Login Simplificadas** - Seguindo práticas do mercado

---

## Problema Atual

### 1. Sem Landing Page
- ❌ Não há página inicial explicando o produto
- ❌ Usuários novos não sabem o que é VivaCampo
- ❌ Sem call-to-action para cadastro

### 2. Sem Sistema de Autenticação
- ❌ Não há fluxo de cadastro de usuário
- ❌ Não há autenticação implementada
- ❌ Sem gestão de tenants

### 3. URLs Confusas
```
❌ localhost:3002/app/login        (confuso)
❌ localhost:3001/admin/login      (confuso)

✅ localhost:3002/login            (esperado)
✅ localhost:3002/admin            (esperado)
```

---

## Solução Proposta

### Arquitetura de URLs (Práticas de Mercado)

```
┌─────────────────────────────────────────────────────────────┐
│ Landing Page (Público)                                      │
│ / (localhost:3002)                                          │
│ - Hero com CTA "Começar Grátis"                            │
│ - Features (monitoramento, alertas, análise)                │
│ - Pricing (Free, Professional, Enterprise)                  │
│ - Testimonials                                              │
│ - Footer com links: /login, /signup, /contact              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Autenticação (Público)                                      │
│ /login (localhost:3002/login)                               │
│ - Email + Senha                                             │
│ - "Esqueci minha senha"                                     │
│ - "Não tem conta? Cadastre-se"                              │
│                                                             │
│ /signup (localhost:3002/signup)                             │
│ - Nome, Email, Senha                                        │
│ - Criar tenant automaticamente                              │
│ - "Já tem conta? Faça login"                                │
│                                                             │
│ /forgot-password (localhost:3002/forgot-password)           │
│ - Email para recuperação                                    │
│                                                             │
│ /reset-password/:token (localhost:3002/reset-password/...) │
│ - Nova senha                                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Dashboard do Usuário (Autenticado)                          │
│ /dashboard (localhost:3002/dashboard)                       │
│ - Farms, Fields, Alerts                                     │
│ - Redireciona para /login se não autenticado                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Admin do Sistema (Super Admin)                              │
│ /admin (localhost:3002/admin)                               │
│ - Gerenciar tenants                                         │
│ - Estatísticas globais                                      │
│ - Configurações do sistema                                  │
│ - Requer role: SYSTEM_ADMIN                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Admin do Tenant (Tenant Admin)                              │
│ /settings (localhost:3002/settings)                         │
│ - Gerenciar usuários do tenant                              │
│ - Custom rules/alerts                                       │
│ - Billing                                                   │
│ - Requer role: TENANT_ADMIN                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Fase 1: Landing Page Profissional (1 semana)

### Design System (Já Gerado)

**Estilo**: Minimalism & Swiss Style
**Cores**:
- Primary: `#1E40AF` (Azul profissional)
- Secondary: `#3B82F6` (Azul claro)
- CTA: `#22C55E` (Verde - ação)
- Background: `#EFF6FF` (Azul muito claro)
- Text: `#1E3A8A` (Azul escuro)

**Tipografia**: Poppins (headings) / Open Sans (body)

### Estrutura da Landing Page

**Arquivo**: `services/app-ui/src/app/page.tsx`

```tsx
// services/app-ui/src/app/page.tsx

import { HeroSection } from '@/components/landing/HeroSection';
import { FeaturesSection } from '@/components/landing/FeaturesSection';
import { PricingSection } from '@/components/landing/PricingSection';
import { TestimonialsSection } from '@/components/landing/TestimonialsSection';
import { ContactSection } from '@/components/landing/ContactSection';
import { Footer } from '@/components/landing/Footer';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Floating Navbar */}
      <nav className="fixed top-4 left-4 right-4 z-50 bg-white/80 backdrop-blur-lg rounded-2xl shadow-lg border border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Logo SVG (não emoji) */}
            <svg className="w-8 h-8 text-green-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
            <span className="text-xl font-semibold text-slate-900">VivaCampo</span>
          </div>

          <div className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-slate-600 hover:text-slate-900 transition-colors">
              Recursos
            </a>
            <a href="#pricing" className="text-slate-600 hover:text-slate-900 transition-colors">
              Preços
            </a>
            <a href="#contact" className="text-slate-600 hover:text-slate-900 transition-colors">
              Contato
            </a>
            <a
              href="/login"
              className="text-slate-600 hover:text-slate-900 transition-colors"
            >
              Login
            </a>
            <a
              href="/signup"
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors cursor-pointer"
            >
              Começar Grátis
            </a>
          </div>
        </div>
      </nav>

      {/* Sections */}
      <HeroSection />
      <FeaturesSection />
      <PricingSection />
      <TestimonialsSection />
      <ContactSection />
      <Footer />
    </div>
  );
}
```

### Componente Hero Section

**Arquivo**: `services/app-ui/src/components/landing/HeroSection.tsx`

```tsx
// services/app-ui/src/components/landing/HeroSection.tsx

export function HeroSection() {
  return (
    <section className="pt-32 pb-20 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* Left: Text Content */}
          <div>
            <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-6 leading-tight">
              Inteligência Agrícola via
              <span className="text-green-600"> Satélite</span>
            </h1>

            <p className="text-xl text-slate-600 mb-8 leading-relaxed">
              Monitore suas lavouras em tempo real com imagens de satélite,
              índices de vegetação (NDVI, SAVI) e alertas personalizados.
              Tome decisões baseadas em dados.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <a
                href="/signup"
                className="px-8 py-4 bg-green-600 text-white text-lg font-semibold rounded-lg hover:bg-green-700 transition-colors text-center cursor-pointer"
              >
                Começar Grátis
              </a>
              <a
                href="#features"
                className="px-8 py-4 bg-white text-slate-900 text-lg font-semibold rounded-lg border-2 border-slate-200 hover:border-slate-300 transition-colors text-center cursor-pointer"
              >
                Ver Recursos
              </a>
            </div>

            {/* Social Proof */}
            <div className="mt-8 flex items-center space-x-6">
              <div>
                <div className="flex items-center space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      className="w-5 h-5 text-yellow-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-sm text-slate-600 mt-1">
                  4.9/5 de 500+ agricultores
                </p>
              </div>
            </div>
          </div>

          {/* Right: Dashboard Mockup */}
          <div className="relative">
            <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-2xl border border-gray-200 p-6">
              {/* Mockup do Dashboard */}
              <div className="aspect-video bg-gradient-to-br from-green-50 to-blue-50 rounded-lg flex items-center justify-center">
                <svg className="w-24 h-24 text-green-600" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                </svg>
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-3 gap-4 mt-6">
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <p className="text-2xl font-bold text-green-600">0.75</p>
                  <p className="text-xs text-slate-600">NDVI Médio</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <p className="text-2xl font-bold text-blue-600">12</p>
                  <p className="text-xs text-slate-600">Talhões</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <p className="text-2xl font-bold text-orange-600">3</p>
                  <p className="text-xs text-slate-600">Alertas</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

### Componente Features Section

**Arquivo**: `services/app-ui/src/components/landing/FeaturesSection.tsx`

```tsx
// services/app-ui/src/components/landing/FeaturesSection.tsx

export function FeaturesSection() {
  const features = [
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "Monitoramento por Satélite",
      description: "Imagens de satélite atualizadas semanalmente com resolução de 10m. Acompanhe o desenvolvimento das lavouras sem sair de casa."
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      title: "Índices de Vegetação",
      description: "NDVI, NDWI, SAVI, EVI e mais. Identifique áreas com estresse hídrico, déficit nutricional ou pragas de forma precoce."
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      ),
      title: "Alertas Personalizados",
      description: "Crie regras customizadas via interface visual. Receba notificações quando NDVI < 0.3 por 7 dias, indicando necessidade de irrigação."
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      title: "Histórico Completo",
      description: "Acesse dados históricos desde 2020. Analise tendências, correlacione com precipitação e tome decisões baseadas em séries temporais."
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "Análise de Custos",
      description: "Integre dados de insumos e correlacione com produtividade. Identifique áreas com melhor ROI e otimize aplicações."
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      title: "Multi-Tenant",
      description: "Gerenciamento de múltiplos usuários e fazendas. Perfeito para consultorias agrícolas, cooperativas e empresas com múltiplas operações."
    }
  ];

  return (
    <section id="features" className="py-20 px-4 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Recursos Poderosos
          </h2>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            Tudo que você precisa para monitorar e otimizar suas lavouras em uma única plataforma
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white border border-gray-200 rounded-xl p-8 hover:shadow-lg transition-shadow cursor-pointer"
            >
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-green-600 mb-4">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

### Componente Pricing Section

**Arquivo**: `services/app-ui/src/components/landing/PricingSection.tsx`

```tsx
// services/app-ui/src/components/landing/PricingSection.tsx

export function PricingSection() {
  const plans = [
    {
      name: "Free",
      price: "R$ 0",
      period: "/mês",
      description: "Perfeito para começar",
      features: [
        "1 fazenda",
        "3 talhões",
        "Imagens semanais",
        "NDVI e NDWI",
        "Histórico de 3 meses"
      ],
      cta: "Começar Grátis",
      highlighted: false
    },
    {
      name: "Professional",
      price: "R$ 199",
      period: "/mês",
      description: "Para agricultores profissionais",
      features: [
        "5 fazendas",
        "50 talhões",
        "Imagens a cada 3 dias",
        "Todos os índices (NDVI, SAVI, EVI, etc)",
        "Alertas personalizados ilimitados",
        "Histórico completo desde 2020",
        "Análise de correlação",
        "Suporte prioritário"
      ],
      cta: "Assinar Professional",
      highlighted: true
    },
    {
      name: "Enterprise",
      price: "Customizado",
      period: "",
      description: "Para cooperativas e consultorias",
      features: [
        "Fazendas ilimitadas",
        "Talhões ilimitados",
        "Multi-tenant com gestão de usuários",
        "API dedicada",
        "Imagens diárias",
        "White-label",
        "Treinamento da equipe",
        "SLA garantido"
      ],
      cta: "Falar com Vendas",
      highlighted: false
    }
  ];

  return (
    <section id="pricing" className="py-20 px-4 bg-gradient-to-b from-white to-blue-50">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Planos Transparentes
          </h2>
          <p className="text-xl text-slate-600">
            Escolha o plano ideal para o tamanho da sua operação
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`bg-white rounded-2xl p-8 border-2 ${
                plan.highlighted
                  ? 'border-green-600 shadow-2xl scale-105'
                  : 'border-gray-200'
              }`}
            >
              {plan.highlighted && (
                <div className="bg-green-600 text-white text-sm font-semibold px-3 py-1 rounded-full inline-block mb-4">
                  Mais Popular
                </div>
              )}

              <h3 className="text-2xl font-bold text-slate-900 mb-2">
                {plan.name}
              </h3>
              <p className="text-slate-600 mb-6">{plan.description}</p>

              <div className="mb-6">
                <span className="text-5xl font-bold text-slate-900">
                  {plan.price}
                </span>
                <span className="text-slate-600">{plan.period}</span>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, fIndex) => (
                  <li key={fIndex} className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-slate-600">{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href="/signup"
                className={`block w-full py-3 text-center font-semibold rounded-lg transition-colors cursor-pointer ${
                  plan.highlighted
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-slate-100 text-slate-900 hover:bg-slate-200'
                }`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

---

## Fase 2: Sistema de Autenticação (2 semanas)

### 2.1 Domain Layer: User & Tenant Entities

**Arquivo**: `services/api/app/domain/entities/user.py`

```python
# services/api/app/domain/entities/user.py

from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """
    Roles de usuário com níveis de permissão.

    Ver detalhes completos em: PERMISSIONS_AND_ROLES_ARCHITECTURE.md
    """
    SYSTEM_ADMIN = "system_admin"  # Admin global (equipe VivaCampo)
    TENANT_ADMIN = "tenant_admin"  # Admin do tenant (owner)
    EDITOR = "editor"              # Colaborador (cria/edita suas fazendas)
    VIEWER = "viewer"              # Somente leitura

class User(BaseModel):
    """
    Domain Entity - User.

    Business Rules:
    - Email deve ser único globalmente
    - Senha deve ter mínimo 8 caracteres (validado no DTO)
    - Usuário deve pertencer a um tenant (exceto SYSTEM_ADMIN)
    - Primeiro usuário (signup) é TENANT_ADMIN
    - Usuários convidados são EDITOR ou VIEWER (escolha do TENANT_ADMIN)

    Permissões por Role:
    - SYSTEM_ADMIN: Acesso total ao sistema
    - TENANT_ADMIN: Gerencia tenant, billing, usuários, todas as fazendas
    - EDITOR: Cria/edita fazendas próprias, vê todas
    - VIEWER: Somente leitura

    Ver detalhes completos em: PERMISSIONS_AND_ROLES_ARCHITECTURE.md
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None  # None apenas para SYSTEM_ADMIN
    email: EmailStr
    password_hash: str  # Hash bcrypt
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)  # Default para convidados

    # Status
    is_active: bool = Field(default=True)
    is_email_verified: bool = Field(default=False)
    email_verification_token: str | None = None

    # Reset de senha
    password_reset_token: str | None = None
    password_reset_expires_at: datetime | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid"
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Email lowercase"""
        return v.lower().strip()

    @field_validator('tenant_id')
    @classmethod
    def validate_tenant_id(cls, v: UUID | None, info) -> UUID | None:
        """SYSTEM_ADMIN não precisa de tenant_id"""
        if 'role' in info.data:
            role = info.data['role']
            if role == UserRole.SYSTEM_ADMIN:
                return None
            elif v is None:
                raise ValueError("Non-system-admin users must have tenant_id")
        return v
```

**Arquivo**: `services/api/app/domain/entities/tenant.py`

```python
# services/api/app/domain/entities/tenant.py

from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class TenantPlan(str, Enum):
    """Planos de assinatura"""
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class TenantStatus(str, Enum):
    """Status do tenant"""
    ACTIVE = "active"
    SUSPENDED = "suspended"  # Não pagou
    CANCELLED = "cancelled"  # Cancelado

class Tenant(BaseModel):
    """
    Domain Entity - Tenant (organização/empresa).

    Business Rules:
    - Nome deve ser único
    - Plano FREE tem limites (1 fazenda, 3 talhões)
    - Status SUSPENDED bloqueia acesso
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=50)  # URL-friendly

    # Assinatura
    plan: TenantPlan = Field(default=TenantPlan.FREE)
    status: TenantStatus = Field(default=TenantStatus.ACTIVE)

    # Billing
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    trial_ends_at: datetime | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid"
    )

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Slug deve ser lowercase e sem espaços"""
        slug = v.lower().strip().replace(' ', '-')
        if not slug.replace('-', '').isalnum():
            raise ValueError("Slug must be alphanumeric with hyphens")
        return slug

    def is_accessible(self) -> bool:
        """Verifica se tenant pode acessar sistema"""
        return self.status == TenantStatus.ACTIVE
```

### 2.2 Sistema de Permissões e Roles

VivaCampo implementa um **sistema de permissões customizável** onde o TENANT_ADMIN escolhe o nível de acesso ao convidar cada usuário.

#### Resumo de Roles

| Role | Descrição | Quando Usar |
|------|-----------|-------------|
| **SYSTEM_ADMIN** | Admin global da plataforma | Equipe VivaCampo |
| **TENANT_ADMIN** | Owner do tenant (primeiro usuário) | Proprietário da fazenda/cooperativa |
| **EDITOR** | Colaborador (cria/edita fazendas próprias) | Agricultor, consultor junior |
| **VIEWER** | Somente leitura | Cliente, auditor, investidor |

#### Permissões Principais

**TENANT_ADMIN**:
- ✅ Criar/editar/apagar TODAS as fazendas do tenant
- ✅ Convidar usuários (EDITOR ou VIEWER)
- ✅ Gerenciar billing e planos
- ✅ Configurações do tenant

**EDITOR**:
- ✅ Criar fazendas (limite do plano)
- ✅ Editar fazendas que ELE criou
- ✅ Ver TODAS as fazendas do tenant (read-only nas de outros)
- ❌ Convidar usuários
- ❌ Gerenciar billing

**VIEWER**:
- ✅ Ver fazendas, imagens, índices, alertas
- ❌ Criar ou editar qualquer coisa

#### Fluxo de Convite

Quando TENANT_ADMIN convida um usuário, ele escolhe entre:

1. **EDITOR** (Colaborativo) - Para membros da equipe que gerenciam fazendas
2. **VIEWER** (Somente Leitura) - Para clientes, auditores, parceiros

**Documentação Completa**: Ver [PERMISSIONS_AND_ROLES_ARCHITECTURE.md](PERMISSIONS_AND_ROLES_ARCHITECTURE.md) para:
- Tabela completa de permissões
- Implementação em todas as camadas (Domain, Application, Presentation, Frontend)
- Guards e validações
- Use cases com verificação de ownership
- UI de convite com escolha de role
- Casos de uso reais (consultoria, cooperativa, fazenda)

---

### 2.3 Application Layer: Auth Use Cases

**Arquivo**: `services/api/app/application/use_cases/auth/signup.py`

```python
# services/api/app/application/use_cases/auth/signup.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
import bcrypt
import secrets

from app.domain.entities.user import User, UserRole
from app.domain.entities.tenant import Tenant, TenantPlan
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.tenant_repository import ITenantRepository
from app.application.exceptions import DuplicateEmailError

class SignupCommand(BaseModel):
    """Command para cadastro de usuário"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=2, max_length=100)
    company_name: str = Field(min_length=2, max_length=100)

    model_config = ConfigDict(frozen=True)

class SignupUseCase:
    """
    Use Case - Cadastro de novo usuário.

    Cria automaticamente:
    1. Tenant (organização)
    2. User (primeiro usuário como TENANT_ADMIN)
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        tenant_repository: ITenantRepository
    ):
        self.user_repository = user_repository
        self.tenant_repository = tenant_repository

    async def execute(self, command: SignupCommand) -> tuple[User, Tenant]:
        """
        Executa cadastro.

        Returns:
            (user, tenant) criados

        Raises:
            DuplicateEmailError: Se email já existe
        """
        # 1. Verificar se email já existe
        existing_user = await self.user_repository.find_by_email(command.email)
        if existing_user:
            raise DuplicateEmailError(f"Email {command.email} already registered")

        # 2. Criar Tenant (organização)
        tenant = Tenant(
            name=command.company_name,
            slug=self._generate_slug(command.company_name),
            plan=TenantPlan.FREE
        )
        saved_tenant = await self.tenant_repository.save(tenant)

        # 3. Hash da senha
        password_hash = self._hash_password(command.password)

        # 4. Criar User (primeiro usuário como TENANT_ADMIN)
        user = User(
            tenant_id=saved_tenant.id,
            email=command.email,
            password_hash=password_hash,
            full_name=command.full_name,
            role=UserRole.TENANT_ADMIN,  # Primeiro usuário é admin
            email_verification_token=secrets.token_urlsafe(32)
        )
        saved_user = await self.user_repository.save(user)

        # TODO: Enviar email de verificação (async, não bloqueia signup)

        return saved_user, saved_tenant

    def _hash_password(self, password: str) -> str:
        """Hash bcrypt da senha"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _generate_slug(self, name: str) -> str:
        """Gera slug único a partir do nome"""
        import re
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        # Adicionar sufixo aleatório para garantir unicidade
        slug = f"{slug}-{secrets.token_hex(4)}"
        return slug
```

### 2.4 Estratégia de Verificação de Email (Não Bloqueante)

**Decisão de Design**: Verificação de email NÃO bloqueia acesso ao sistema.

#### Por Que Não Bloquear?

1. **Melhor UX** - Usuário pode começar a usar imediatamente após signup
2. **Maior conversão** - Menos fricção = mais cadastros completados
3. **Progressive enhancement** - Funcionalidades avançadas exigem verificação

#### Como Funciona

```
┌────────────────────────────────────────────────────────────┐
│ 1. Usuário se cadastra                                     │
│    - Cria conta com email/senha                            │
│    - is_email_verified = False                             │
│    - email_verification_token = gerado                     │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Auto-login (JWT gerado)                                 │
│    - Usuário é redirecionado para /dashboard               │
│    - Token JWT contém is_email_verified = False            │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Email de verificação enviado (async)                    │
│    - Email enviado em background                           │
│    - Não bloqueia signup/login                             │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Banner no Dashboard                                     │
│    - "📧 Verifique seu email para desbloquear recursos"    │
│    - Link "Reenviar email de verificação"                  │
│    - Banner visível até verificação                        │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Funcionalidades Básicas Disponíveis                     │
│    ✅ Criar fazendas (limite plano FREE)                   │
│    ✅ Visualizar imagens de satélite                       │
│    ✅ Ver índices (NDVI, NDWI)                             │
│    ✅ Criar alertas (limite plano FREE)                    │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ 6. Funcionalidades Bloqueadas (Requerem Verificação)       │
│    ❌ Convidar outros usuários                             │
│    ❌ Fazer upgrade para plano pago                        │
│    ❌ Exceder limites do plano FREE                        │
│    ❌ Configurar billing (Stripe)                          │
└────────────────────────────────────────────────────────────┘
```

#### Quando EXIGIR Verificação?

**Funcionalidades que REQUEREM email verificado:**

| Funcionalidade | Por Que? |
|----------------|----------|
| **Convidar usuários** | Prevenir spam, garantir que é um tenant legítimo |
| **Upgrade para plano pago** | Necessário para billing e comunicação de cobrança |
| **Exceder limites FREE** | Ex: criar 4ª fazenda requer verificação + upgrade |
| **Configurar billing** | Stripe precisa de email verificado |
| **Exportar dados** | Funcionalidade premium, requer verificação |

**Funcionalidades que NÃO REQUEREM verificação:**

| Funcionalidade | Por Que? |
|----------------|----------|
| **Criar fazendas (dentro do limite FREE)** | Deixar usuário testar produto |
| **Ver imagens/índices** | Funcionalidade core, deve ser acessível |
| **Criar alertas (dentro do limite FREE)** | Experiência completa |
| **Visualizar dashboard** | Acesso básico garantido |

#### Implementação - Banner de Verificação

**Arquivo**: `services/app-ui/src/components/dashboard/EmailVerificationBanner.tsx`

```tsx
// services/app-ui/src/components/dashboard/EmailVerificationBanner.tsx

'use client';

import { useState } from 'react';

interface Props {
  userEmail: string;
  isEmailVerified: boolean;
}

export function EmailVerificationBanner({ userEmail, isEmailVerified }: Props) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  if (isEmailVerified) {
    return null; // Não mostrar banner se já verificado
  }

  const handleResendEmail = async () => {
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:8000/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ email: userEmail })
      });

      if (response.ok) {
        setMessage('✅ Email de verificação reenviado! Verifique sua caixa de entrada.');
      } else {
        setMessage('❌ Erro ao reenviar email. Tente novamente mais tarde.');
      }
    } catch {
      setMessage('❌ Erro ao reenviar email. Tente novamente mais tarde.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            📧 Verifique seu email
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>
              Enviamos um email de verificação para <strong>{userEmail}</strong>.
              Algumas funcionalidades (convidar usuários, upgrade de plano) requerem
              verificação de email.
            </p>
          </div>
          <div className="mt-4 flex items-center space-x-4">
            <button
              onClick={handleResendEmail}
              disabled={loading}
              className="text-sm font-medium text-yellow-800 hover:text-yellow-900 underline disabled:opacity-50"
            >
              {loading ? 'Reenviando...' : 'Reenviar email de verificação'}
            </button>
          </div>
          {message && (
            <p className="mt-2 text-sm text-yellow-700">{message}</p>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Uso no Dashboard:**

```tsx
// services/app-ui/src/app/dashboard/page.tsx

import { EmailVerificationBanner } from '@/components/dashboard/EmailVerificationBanner';

export default function DashboardPage() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <div className="p-6">
      {/* Banner de Verificação (mostra apenas se não verificado) */}
      <EmailVerificationBanner
        userEmail={user.email}
        isEmailVerified={user.is_email_verified}
      />

      {/* Resto do dashboard */}
      <h1>Dashboard</h1>
      {/* ... */}
    </div>
  );
}
```

#### Implementação - Verificação de Email Backend

**Arquivo**: `services/api/app/application/use_cases/auth/verify_email.py`

```python
# services/api/app/application/use_cases/auth/verify_email.py

from pydantic import BaseModel, ConfigDict
from app.domain.repositories.user_repository import IUserRepository
from app.application.exceptions import InvalidTokenError

class VerifyEmailCommand(BaseModel):
    """Command para verificar email"""
    token: str
    model_config = ConfigDict(frozen=True)

class VerifyEmailUseCase:
    """Use Case - Verificar email do usuário"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self, command: VerifyEmailCommand) -> None:
        """
        Verifica email usando token.

        Raises:
            InvalidTokenError: Token inválido ou expirado
        """
        # Buscar usuário pelo token
        user = await self.user_repository.find_by_verification_token(command.token)

        if not user:
            raise InvalidTokenError("Invalid or expired verification token")

        # Marcar email como verificado
        user.is_email_verified = True
        user.email_verification_token = None

        await self.user_repository.save(user)
```

#### Bloqueio de Funcionalidades - Guard Decorator

**Arquivo**: `services/api/app/presentation/dependencies.py`

```python
# services/api/app/presentation/dependencies.py

from fastapi import HTTPException, status, Depends
from app.domain.entities.user import User
from app.presentation.auth import get_current_user

async def require_verified_email(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency que REQUER email verificado.

    Usar em rotas que exigem verificação:
    - Convidar usuários
    - Upgrade de plano
    - Configurar billing
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email to access this feature."
        )

    return current_user
```

**Uso nas Rotas:**

```python
# Exemplo: Rota que REQUER email verificado
@router.post("/invitations/send")
async def send_invitation(
    request: SendInvitationDTO,
    current_user: User = Depends(require_verified_email)  # ← Guard
):
    """
    Envia convite para novo usuário.
    REQUER email verificado.
    """
    # Lógica de convite...
    pass


# Exemplo: Rota que NÃO requer verificação
@router.post("/farms/")
async def create_farm(
    request: CreateFarmDTO,
    current_user: User = Depends(get_current_user)  # ← Apenas autenticação
):
    """
    Cria fazenda (dentro do limite FREE).
    NÃO requer email verificado.
    """
    # Lógica de criação...
    pass
```

#### Checklist de Implementação

- [ ] User entity tem campo `is_email_verified` (default=False)
- [ ] User entity tem campo `email_verification_token`
- [ ] SignupUseCase gera token de verificação
- [ ] SignupUseCase envia email em background (não bloqueia)
- [ ] LoginUseCase permite login mesmo se `is_email_verified=False`
- [ ] JWT token contém `is_email_verified` no payload
- [ ] Frontend mostra banner de verificação no dashboard
- [ ] Frontend tem botão "Reenviar email"
- [ ] Backend tem endpoint `POST /auth/verify-email/:token`
- [ ] Backend tem endpoint `POST /auth/resend-verification`
- [ ] Backend tem guard `require_verified_email` para rotas críticas
- [ ] Rotas de convite/billing usam `require_verified_email` guard
- [ ] Rotas básicas (criar fazenda, ver imagens) NÃO usam guard

---

**Arquivo**: `services/api/app/application/use_cases/auth/login.py`

```python
# services/api/app/application/use_cases/auth/login.py

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, timedelta
import bcrypt
import jwt

from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.tenant_repository import ITenantRepository
from app.application.exceptions import InvalidCredentialsError, TenantSuspendedError
from app.core.settings import settings

class LoginCommand(BaseModel):
    """Command para login"""
    email: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)

class LoginResponse(BaseModel):
    """Response do login"""
    access_token: str
    token_type: str = "bearer"
    user: dict
    tenant: dict

class LoginUseCase:
    """Use Case - Login de usuário"""

    def __init__(
        self,
        user_repository: IUserRepository,
        tenant_repository: ITenantRepository
    ):
        self.user_repository = user_repository
        self.tenant_repository = tenant_repository

    async def execute(self, command: LoginCommand) -> LoginResponse:
        """
        Executa login.

        Returns:
            LoginResponse com JWT token

        Raises:
            InvalidCredentialsError: Email ou senha incorretos
            TenantSuspendedError: Tenant suspenso
        """
        # 1. Buscar usuário por email
        user = await self.user_repository.find_by_email(command.email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        # 2. Verificar senha
        if not self._verify_password(command.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        # 3. Verificar se usuário está ativo
        if not user.is_active:
            raise InvalidCredentialsError("User account is inactive")

        # 4. Se não é SYSTEM_ADMIN, verificar tenant
        tenant = None
        if user.tenant_id:
            tenant = await self.tenant_repository.find_by_id(user.tenant_id)
            if not tenant or not tenant.is_accessible():
                raise TenantSuspendedError("Organization account is suspended")

        # 5. Atualizar last_login_at
        user.last_login_at = datetime.utcnow()
        await self.user_repository.save(user)

        # 6. Gerar JWT token
        access_token = self._generate_token(user)

        # 7. Retornar resposta
        return LoginResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            },
            tenant={
                "id": str(tenant.id) if tenant else None,
                "name": tenant.name if tenant else None,
                "plan": tenant.plan if tenant else None
            }
        )

    def _verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verifica senha contra hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    def _generate_token(self, user: User) -> str:
        """Gera JWT token"""
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "exp": datetime.utcnow() + timedelta(days=7)
        }

        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm="HS256"
        )
```

### 2.5 Presentation Layer: Auth Router

**Arquivo**: `services/api/app/presentation/routers/auth_router.py`

```python
# services/api/app/presentation/routers/auth_router.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated

from app.presentation.dtos.auth_dtos import (
    SignupRequestDTO,
    LoginRequestDTO,
    LoginResponseDTO
)
from app.application.use_cases.auth.signup import (
    SignupUseCase,
    SignupCommand
)
from app.application.use_cases.auth.login import (
    LoginUseCase,
    LoginCommand
)
from app.application.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    TenantSuspendedError
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/signup",
    response_model=LoginResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up new user"
)
async def signup(
    request: SignupRequestDTO,
    use_case: Annotated[SignupUseCase, Depends(get_signup_use_case)]
):
    """
    Create new user account and organization.

    - Creates tenant (organization) automatically
    - First user becomes TENANT_ADMIN
    - Sends email verification (TODO)
    - Returns JWT token for immediate login
    """
    command = SignupCommand(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        company_name=request.company_name
    )

    try:
        user, tenant = await use_case.execute(command)

        # Auto-login após cadastro
        login_command = LoginCommand(
            email=request.email,
            password=request.password
        )
        login_use_case = get_login_use_case()
        login_response = await login_use_case.execute(login_command)

        return login_response

    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/login",
    response_model=LoginResponseDTO,
    summary="Login user"
)
async def login(
    request: LoginRequestDTO,
    use_case: Annotated[LoginUseCase, Depends(get_login_use_case)]
):
    """
    Authenticate user and return JWT token.

    - Verifies email and password
    - Checks if tenant is active
    - Returns access token valid for 7 days
    """
    command = LoginCommand(
        email=request.email,
        password=request.password
    )

    try:
        response = await use_case.execute(command)
        return response

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except TenantSuspendedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
```

---

## Fase 3: Frontend de Autenticação (1 semana)

### 3.1 Página de Login

**Arquivo**: `services/app-ui/src/app/login/page.tsx`

```tsx
// services/app-ui/src/app/login/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await response.json();

      // Salvar token no localStorage
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('tenant', JSON.stringify(data.tenant));

      // Redirecionar para dashboard
      router.push('/dashboard');

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2">
            <svg className="w-10 h-10 text-green-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
            <span className="text-2xl font-bold text-slate-900">VivaCampo</span>
          </Link>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Bem-vindo de volta
          </h1>
          <p className="text-slate-600 mb-8">
            Entre na sua conta para acessar o dashboard
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                placeholder="seu@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">
                Senha
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className="rounded border-gray-300 text-green-600 focus:ring-green-600" />
                <span className="ml-2 text-sm text-slate-600">Lembrar de mim</span>
              </label>

              <Link href="/forgot-password" className="text-sm text-green-600 hover:text-green-700">
                Esqueceu a senha?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-600">
              Não tem uma conta?{' '}
              <Link href="/signup" className="text-green-600 hover:text-green-700 font-semibold">
                Cadastre-se grátis
              </Link>
            </p>
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-slate-600 hover:text-slate-900">
            ← Voltar para página inicial
          </Link>
        </div>
      </div>
    </div>
  );
}
```

### 3.2 Página de Cadastro

**Arquivo**: `services/app-ui/src/app/signup/page.tsx`

```tsx
// services/app-ui/src/app/signup/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    company_name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Signup failed');
      }

      const data = await response.json();

      // Salvar token (auto-login após cadastro)
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('tenant', JSON.stringify(data.tenant));

      // Redirecionar para dashboard
      router.push('/dashboard');

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar conta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2">
            <svg className="w-10 h-10 text-green-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
            <span className="text-2xl font-bold text-slate-900">VivaCampo</span>
          </Link>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Criar conta grátis
          </h1>
          <p className="text-slate-600 mb-8">
            Comece a monitorar suas lavouras agora
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 mb-2">
                Nome Completo
              </label>
              <input
                id="full_name"
                type="text"
                required
                minLength={2}
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                placeholder="João Silva"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                placeholder="joao@fazenda.com"
              />
            </div>

            <div>
              <label htmlFor="company_name" className="block text-sm font-medium text-slate-700 mb-2">
                Nome da Fazenda/Empresa
              </label>
              <input
                id="company_name"
                type="text"
                required
                minLength={2}
                value={formData.company_name}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                placeholder="Fazenda Santa Maria"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">
                Senha
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                placeholder="••••••••"
              />
              <p className="mt-2 text-sm text-slate-500">
                Mínimo de 8 caracteres
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Criando conta...' : 'Criar conta grátis'}
            </button>

            <p className="text-xs text-slate-500 text-center">
              Ao criar uma conta, você concorda com nossos{' '}
              <Link href="/terms" className="text-green-600 hover:text-green-700">
                Termos de Uso
              </Link>{' '}
              e{' '}
              <Link href="/privacy" className="text-green-600 hover:text-green-700">
                Política de Privacidade
              </Link>
            </p>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-600">
              Já tem uma conta?{' '}
              <Link href="/login" className="text-green-600 hover:text-green-700 font-semibold">
                Faça login
              </Link>
            </p>
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-slate-600 hover:text-slate-900">
            ← Voltar para página inicial
          </Link>
        </div>
      </div>
    </div>
  );
}
```

---

## Fase 4: Proteção de Rotas e Middleware (3 dias)

### 4.1 Middleware de Autenticação

**Arquivo**: `services/app-ui/src/middleware.ts`

```typescript
// services/app-ui/src/middleware.ts

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Rotas públicas (não precisam autenticação)
const PUBLIC_ROUTES = [
  '/',
  '/login',
  '/signup',
  '/forgot-password',
  '/reset-password',
  '/terms',
  '/privacy'
];

// Rotas que precisam SYSTEM_ADMIN
const SYSTEM_ADMIN_ROUTES = ['/admin'];

// Rotas que precisam TENANT_ADMIN
const TENANT_ADMIN_ROUTES = ['/settings'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Verificar se é rota pública
  const isPublicRoute = PUBLIC_ROUTES.some(route =>
    pathname === route || pathname.startsWith(`${route}/`)
  );

  if (isPublicRoute) {
    return NextResponse.next();
  }

  // Obter token do cookie ou header
  const token = request.cookies.get('access_token')?.value ||
                request.headers.get('authorization')?.replace('Bearer ', '');

  if (!token) {
    // Redirecionar para login
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Decodificar token (simplificado - validar no backend)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));

    // Verificar rotas de SYSTEM_ADMIN
    if (SYSTEM_ADMIN_ROUTES.some(route => pathname.startsWith(route))) {
      if (payload.role !== 'system_admin') {
        return NextResponse.redirect(new URL('/dashboard', request.url));
      }
    }

    // Verificar rotas de TENANT_ADMIN
    if (TENANT_ADMIN_ROUTES.some(route => pathname.startsWith(route))) {
      if (payload.role !== 'tenant_admin' && payload.role !== 'system_admin') {
        return NextResponse.redirect(new URL('/dashboard', request.url));
      }
    }

    return NextResponse.next();

  } catch {
    // Token inválido
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
```

---

## Fase 5: Migração de URLs (2 dias)

### 5.1 Atualizar Next.js Config

**Arquivo**: `services/app-ui/next.config.js`

```javascript
// services/app-ui/next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remover /app prefix das rotas
  basePath: '',

  async rewrites() {
    return [
      // Legacy redirects
      {
        source: '/app/login',
        destination: '/login',
      },
      {
        source: '/app/:path*',
        destination: '/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

---

## Documentos Relacionados

Este plano trabalha em conjunto com outros documentos de arquitetura:

### 📋 [PERMISSIONS_AND_ROLES_ARCHITECTURE.md](PERMISSIONS_AND_ROLES_ARCHITECTURE.md)
**Sistema de Permissões Customizável**

Define os 4 roles do sistema (SYSTEM_ADMIN, TENANT_ADMIN, EDITOR, VIEWER) e como implementar permissões em todas as camadas.

**O que contém**:
- Tabela completa de permissões por role
- Implementação do campo `created_by_user_id` em Farm (ownership)
- Guards de permissão (`require_tenant_admin`, `require_editor`, etc.)
- Use Cases com verificação de ownership
- UI de convite com escolha de role (EDITOR vs VIEWER)
- Casos de uso reais (consultoria, cooperativa, fazenda)

**Quando consultar**:
- Ao implementar criação/edição de fazendas (verificar ownership)
- Ao criar rotas de API (escolher guard correto)
- Ao implementar convite de usuários (choice de role)
- Ao testar permissões (casos de teste por role)

### 🏗️ [HEXAGONAL_ARCHITECTURE_PLAN.md](HEXAGONAL_ARCHITECTURE_PLAN.md)
Arquitetura geral do sistema com camadas Domain, Application, Infrastructure, Presentation.

### 📊 [INDICATORS_AND_FRONTEND_INTEGRATION.md](INDICATORS_AND_FRONTEND_INTEGRATION.md)
Integração de índices de vegetação (NDVI, SAVI) com frontend TypeScript.

---

## Resumo do Plano

| Fase | Duração | Entregáveis |
|------|---------|-------------|
| **Fase 1: Landing Page** | 1 semana | Landing page com hero, features, pricing, testimonials |
| **Fase 2: Backend Auth** | 2 semanas | Domain entities (User, Tenant), 4 roles (SYSTEM_ADMIN, TENANT_ADMIN, EDITOR, VIEWER), use cases, repositories, API routes |
| **Fase 3: Frontend Auth** | 1 semana | Páginas de login, signup, forgot-password |
| **Fase 4: Proteção de Rotas** | 3 dias | Middleware, guards customizados por role, verificação de ownership |
| **Fase 5: Migração de URLs** | 2 dias | URLs simplificadas, redirects |

**Total**: ~4-5 semanas

---

## Próximos Passos Imediatos

1. **Validar design** da landing page gerado
2. **Implementar backend** de autenticação primeiro (Fase 2)
3. **Criar landing page** (Fase 1) em paralelo
4. **Integrar frontend** com backend (Fase 3)
5. **Proteger rotas** com middleware (Fase 4)
6. **Simplificar URLs** (Fase 5)

Quer que eu comece implementando alguma fase específica agora?
