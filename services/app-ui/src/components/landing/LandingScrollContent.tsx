'use client'

import Image from 'next/image'
import Link from 'next/link'
import { TrackLink } from './TrackLink'

const featureHighlights = [
    {
        title: 'NDVI em tempo real',
        description: 'Mapas vivos com detecção de estresse hídrico e vigor vegetal em minutos.',
    },
    {
        title: 'Alertas inteligentes',
        description: 'IA identifica anomalias e recomenda ações antes que o dano aconteça.',
    },
    {
        title: 'Histórico multissafra',
        description: 'Comparações sazonais e insights de produtividade em toda a operação.',
    },
    {
        title: 'Camada radar',
        description: 'Monitoramento contínuo mesmo com nuvens densas.',
    },
    {
        title: 'Fluxos automatizados',
        description: 'Processamento semanal, alertas e relatórios sem esforço manual.',
    },
    {
        title: 'Multi-tenant seguro',
        description: 'Controle por papéis e isolamento de dados por organização.',
    },
]

const pricingPlans = [
    {
        name: 'Explorador',
        price: 'R$0',
        description: 'Para começar a testar',
        features: ['Até 50 hectares', 'Imagens mensais', 'Relatórios básicos'],
        cta: 'Começar grátis',
        highlighted: false,
    },
    {
        name: 'Profissional',
        price: 'R$499',
        description: 'Para produtores sérios',
        features: ['Até 5.000 hectares', 'Imagens diárias', 'Alertas em tempo real', 'API access'],
        cta: 'Começar agora',
        highlighted: true,
    },
    {
        name: 'Enterprise',
        price: 'Custom',
        description: 'Operações em escala',
        features: ['Hectares ilimitados', 'SLA garantido', 'White-label', 'Equipe dedicada'],
        cta: 'Falar com vendas',
        highlighted: false,
    },
]

const apiHighlights = [
    {
        title: 'API Geoespacial',
        description: 'Endpoints REST com tiles, índices e dados agronômicos versionados.',
    },
    {
        title: 'Integrações',
        description: 'Conecte ERPs, CRMs e fluxos de campo com webhooks e exports.',
    },
    {
        title: 'Segurança LGPD',
        description: 'Camadas de autenticação, rate limiting e logs auditáveis.',
    },
]

type LandingScrollContentProps = {
    displayFontClassName: string
    heroCtaText: string
}

export function LandingScrollContent({ displayFontClassName, heroCtaText }: LandingScrollContentProps) {
    return (
        <div className="w-screen min-w-[360px] overflow-x-hidden pb-24">
            <main id="content" className="relative">
                <section id="hero" className="hero-scroll-layer relative isolate flex min-h-screen items-center overflow-x-hidden bg-[#050505] px-6 pb-20 pt-32">
                    <div className="absolute inset-0 z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.08),transparent_60%),radial-gradient(circle_at_70%_10%,rgba(0,255,135,0.08),transparent_50%),radial-gradient(circle_at_50%_90%,rgba(59,130,246,0.09),transparent_55%)]" />

                    <div className="absolute inset-0 z-10">
                        <div className="hero-contrast absolute inset-0 opacity-30" />
                    </div>
                    <div className="relative z-20 mx-auto flex w-full max-w-6xl justify-center px-4 lg:px-6">
                        <div className="flex w-full flex-col items-center text-center lg:max-w-3xl lg:items-center lg:text-center">
                            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-xs uppercase tracking-[0.25em] text-emerald-200">
                                Portal VivaCampo
                            </p>
                            <h1 className={`text-balance text-3xl font-semibold leading-tight sm:text-5xl lg:text-6xl ${displayFontClassName}`}>
                                Não é só agricultura.<br />
                                É <span className="text-cyan-300">inteligência planetária</span>.
                            </h1>
                            <p className="mt-6 text-lg text-gray-200 sm:text-xl">
                                Dados em tempo real de 127 satélites analisando 850 milhões de hectares.
                            </p>
                            <div className="mt-8 flex flex-col gap-4 sm:flex-row lg:justify-start">
                                <TrackLink
                                    href="/signup"
                                    goal="Signup Started"
                                    metadata={{ placement: 'hero', variant: heroCtaText }}
                                    className="min-h-touch min-w-touch rounded-full bg-blue-600 px-8 py-4 text-center text-sm font-semibold uppercase tracking-wide transition-colors hover:bg-blue-500 cursor-pointer"
                                >
                                    {heroCtaText}
                                </TrackLink>
                                <a
                                    href="#journey"
                                    className="min-h-touch min-w-touch rounded-full border border-white/20 px-8 py-4 text-center text-sm font-semibold uppercase tracking-wide text-white transition-colors hover:border-cyan-300 hover:text-cyan-300 cursor-pointer"
                                >
                                    Ver a jornada
                                </a>
                                <a
                                    href="#recursos"
                                    className="min-h-touch min-w-touch rounded-full border border-emerald-400/40 px-8 py-4 text-center text-sm font-semibold uppercase tracking-wide text-emerald-200 transition-colors hover:border-emerald-300 hover:text-emerald-100 cursor-pointer"
                                >
                                    Pular intro
                                </a>
                            </div>
                            <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-400 lg:justify-start">
                                <span>127 satélites integrados</span>
                                <span>850M hectares monitorados</span>
                                <span>Precisão de 98.7%</span>
                            </div>
                        </div>
                    </div>
                    <a
                        href="#journey"
                        className="min-h-touch min-w-touch absolute bottom-10 left-1/2 z-20 flex -translate-x-1/2 flex-col items-center gap-2 text-xs uppercase tracking-[0.3em] text-gray-400 cursor-pointer px-3 py-2"
                    >
                        <span>Scroll</span>
                        <span className="h-12 w-px bg-gradient-to-b from-cyan-300/60 to-transparent" />
                    </a>
                </section>

                <section id="journey" className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto grid max-w-7xl gap-16 lg:grid-cols-[1.2fr_1fr] lg:items-center">
                        <div className="farm-zoom-card relative overflow-hidden rounded-[32px] border border-white/10 bg-white/5 p-6">
                            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl">
                                <Image
                                    src="/landing/farm-zoom.png"
                                    alt="Zoom na fazenda com linhas inteligentes"
                                    width={960}
                                    height={720}
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 60vw, 560px"
                                    className="h-full w-full rounded-2xl object-cover opacity-70"
                                />
                                <svg
                                    className="farm-lines pointer-events-none absolute inset-0"
                                    viewBox="0 0 800 600"
                                    fill="none"
                                >
                                    <path
                                        d="M140 180L260 140L360 190L480 160L620 200L700 160"
                                        stroke="#00FF87"
                                        strokeWidth="3"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                    <path
                                        d="M180 260L300 230L420 260L560 240L680 280"
                                        stroke="#38BDF8"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                    <path
                                        d="M120 360L260 330L380 360L520 340L660 370"
                                        stroke="#60A5FA"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            </div>
                            <div className="absolute inset-0 rounded-[32px] border border-emerald-400/20" />
                        </div>
                        <div className="rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">Capítulo 1</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-4xl ${displayFontClassName}`}>
                                A escala da fazenda, monitorada por IA
                            </h2>
                            <p className="mt-6 text-base text-gray-300 sm:text-lg">
                                Talhões mapeados com precisão, overlays de produtividade e alertas contextuais para decisões no tempo certo.
                            </p>
                            <ul className="mt-6 space-y-3 text-sm text-gray-300">
                                <li className="flex items-center gap-3">
                                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                                    Delimitação automática e tracking de evolução.
                                </li>
                                <li className="flex items-center gap-3">
                                    <span className="h-2 w-2 rounded-full bg-cyan-300" />
                                    Análises de estresse hídrico em tempo real.
                                </li>
                                <li className="flex items-center gap-3">
                                    <span className="h-2 w-2 rounded-full bg-blue-400" />
                                    Indicadores comparativos por safra.
                                </li>
                            </ul>
                            <a
                                href="#planos"
                                className="mt-8 inline-flex min-h-touch min-w-touch rounded-full border border-white/20 px-6 py-3 text-xs font-semibold uppercase tracking-wider text-white transition-colors hover:border-cyan-300 hover:text-cyan-300 cursor-pointer"
                            >
                                Ver fazenda exemplo
                            </a>
                        </div>
                    </div>
                </section>

                <section id="micro" className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto grid max-w-7xl gap-16 lg:grid-cols-[1fr_1.2fr] lg:items-center">
                        <div className="rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Capítulo 2</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-4xl ${displayFontClassName}`}>
                                Do satélite à raiz, o invisível aparece
                            </h2>
                            <p className="mt-6 text-base text-gray-300 sm:text-lg">
                                O micro detalhe da folha com precisão de laboratório. A IA detecta pragas e anomalias antes do olho humano.
                            </p>
                            <div className="micro-card mt-8 rounded-2xl border border-white/10 bg-white/5 p-6">
                                <div className="text-xs uppercase tracking-[0.3em] text-gray-400">Análise completa</div>
                                <div className={`mt-3 text-4xl font-semibold ${displayFontClassName}`}>98.3%</div>
                                <div className="mt-4 flex items-center gap-2 text-sm text-gray-300">
                                    <span className="h-2 w-2 rounded-full bg-red-500 motion-safe:animate-pulse" />
                                    Ferrugem asiática detectada
                                </div>
                                <p className="mt-2 text-xs text-gray-400">Severidade moderada • Área 240m²</p>
                            </div>
                        </div>
                        <div className="micro-visual relative overflow-hidden rounded-[32px] border border-white/10 bg-white/5 p-6">
                            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl">
                                <Image
                                    src="/landing/micro-analysis.png"
                                    alt="Análise micro com scanner e alerta"
                                    width={960}
                                    height={720}
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 60vw, 560px"
                                    className="h-full w-full rounded-2xl object-cover opacity-70"
                                />
                                <div className="absolute inset-10 rounded-3xl border-2 border-emerald-400/60 motion-safe:animate-[pulse_2.5s_ease-in-out_infinite]" />
                            </div>
                        </div>
                    </div>
                </section>

                <section className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto max-w-7xl">
                        <div className="text-center rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-blue-300">Capítulo 3</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-5xl ${displayFontClassName}`}>
                                O sistema operacional da nova era agrícola
                            </h2>
                        </div>
                        <div className="mt-16 grid gap-8 lg:grid-cols-[1.2fr_1fr]">
                            <div className="relative overflow-hidden rounded-[32px] border border-white/10 bg-white/5 p-6">
                                <Image
                                    src="/landing/devices-mockup.png"
                                    alt="Aplicativo VivaCampo em múltiplos dispositivos"
                                    width={980}
                                    height={740}
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 70vw, 620px"
                                    className="h-auto w-full rounded-2xl object-cover"
                                />
                            </div>
                            <div className="grid gap-6">
                                <div className="landing-card-strong rounded-3xl border border-white/10 bg-gradient-to-br from-blue-600/20 to-emerald-600/20 p-6">
                                    <div className={`text-4xl font-semibold ${displayFontClassName}`}>127</div>
                                    <p className="mt-2 text-sm text-gray-300">Satélites integrados</p>
                                </div>
                                <div className="landing-card-strong rounded-3xl border border-white/10 bg-gradient-to-br from-purple-600/20 to-pink-600/20 p-6">
                                    <div className={`text-4xl font-semibold ${displayFontClassName}`}>98.7%</div>
                                    <p className="mt-2 text-sm text-gray-300">Precisão de predição</p>
                                </div>
                                <div className="landing-card-strong rounded-3xl border border-white/10 bg-gradient-to-br from-orange-600/20 to-red-600/20 p-6">
                                    <div className={`text-4xl font-semibold ${displayFontClassName}`}>2.3M</div>
                                    <p className="mt-2 text-sm text-gray-300">Hectares monitorados</p>
                                </div>
                                <div className="landing-card-strong rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-gray-300">
                                    <p className="font-semibold text-white">Clientes em todo o Brasil</p>
                                    <p className="mt-3">“Reduzimos perdas em 18% com alertas de estresse hídrico.”</p>
                                    <p className="mt-4 text-xs text-gray-400">Fazenda Santa Maria</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section id="recursos" className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto max-w-7xl">
                        <div className="max-w-2xl rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">Recursos</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-4xl ${displayFontClassName}`}>
                                Tudo para operar com visão orbital
                            </h2>
                            <p className="mt-4 text-base text-gray-300 sm:text-lg">
                                Do mapa ao insight, cada módulo foi desenhado para reduzir risco e antecipar decisões críticas.
                            </p>
                        </div>
                        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                            {featureHighlights.map((feature) => (
                                <div
                                    key={feature.title}
                                    className="landing-card-strong group rounded-2xl border border-white/10 bg-white/5 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-cyan-300/50 hover:shadow-[0_0_40px_rgba(56,189,248,0.2)] cursor-pointer"
                                >
                                    <div className="mb-4 h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-400/20 to-emerald-400/20" />
                                    <h3 className={`text-lg font-semibold ${displayFontClassName}`}>{feature.title}</h3>
                                    <p className="mt-3 text-sm text-gray-300">{feature.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <section id="planos" className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto max-w-7xl">
                        <div className="text-center rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Planos</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-5xl ${displayFontClassName}`}>
                                Escolha o plano ideal
                            </h2>
                            <p className="mt-4 text-base text-gray-300 sm:text-lg">
                                Planos flexíveis para cada estágio da operação.
                            </p>
                        </div>
                        <div className="mt-14 grid gap-8 lg:grid-cols-3">
                            {pricingPlans.map((plan) => (
                                <div
                                    key={plan.name}
                                    className={`landing-card-strong relative rounded-3xl border p-8 ${plan.highlighted
                                        ? 'border-cyan-300/60 bg-gradient-to-br from-blue-600/20 to-emerald-600/20 shadow-[0_0_50px_rgba(14,165,233,0.35)]'
                                        : 'border-white/10 bg-white/5'
                                        }`}
                                >
                                    {plan.highlighted ? (
                                        <span className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-cyan-300 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-black">
                                            Mais popular
                                        </span>
                                    ) : null}
                                    <h3 className={`text-2xl font-semibold ${displayFontClassName}`}>{plan.name}</h3>
                                    <p className="mt-2 text-sm text-gray-400">{plan.description}</p>
                                    <div className="mt-6 flex items-baseline gap-2">
                                        <span className={`text-4xl font-semibold ${displayFontClassName}`}>{plan.price}</span>
                                        {plan.name !== 'Enterprise' ? <span className="text-sm text-gray-400">/mês</span> : null}
                                    </div>
                                    <ul className="mt-6 space-y-3 text-sm text-gray-300">
                                        {plan.features.map((item) => (
                                            <li key={item} className="flex items-center gap-3">
                                                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                    <TrackLink
                                        href={plan.name === 'Enterprise' ? '/contact' : '/signup'}
                                        goal={plan.name === 'Enterprise' ? 'Demo Requested' : 'Signup Started'}
                                        metadata={{ placement: 'pricing', plan: plan.name }}
                                        className={`mt-8 block min-h-touch min-w-touch rounded-full px-6 py-3 text-center text-sm font-semibold uppercase tracking-wider transition-colors cursor-pointer ${plan.highlighted
                                            ? 'bg-cyan-300 text-black hover:bg-cyan-200'
                                            : 'border border-white/20 text-white hover:border-cyan-300 hover:text-cyan-300'
                                            }`}
                                    >
                                        {plan.cta}
                                    </TrackLink>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <section id="api" className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[1fr_1.1fr] lg:items-center">
                        <div className="rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">API</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-4xl ${displayFontClassName}`}>
                                Infraestrutura pronta para integrar
                            </h2>
                            <p className="mt-4 text-base text-gray-300 sm:text-lg">
                                Acesse dados geoespaciais e insights por API, mantenha sua stack conectada e escale com segurança.
                            </p>
                            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                                <TrackLink
                                    href="/docs"
                                    goal="API Docs Visited"
                                    metadata={{ placement: 'api-section' }}
                                    className="min-h-touch min-w-touch rounded-full border border-white/20 px-6 py-3 text-center text-sm font-semibold uppercase tracking-wider text-white transition-colors hover:border-cyan-300 hover:text-cyan-300 cursor-pointer"
                                >
                                    Ver documentação
                                </TrackLink>
                                <TrackLink
                                    href="/contact"
                                    goal="CTA Click"
                                    metadata={{ placement: 'api-section', plan: 'Enterprise' }}
                                    className="min-h-touch min-w-touch rounded-full bg-emerald-400 px-6 py-3 text-center text-sm font-semibold uppercase tracking-wider text-black transition-colors hover:bg-emerald-300 cursor-pointer"
                                >
                                    Falar com API team
                                </TrackLink>
                            </div>
                        </div>
                        <div className="grid gap-4">
                            {apiHighlights.map((item) => (
                                <div key={item.title} className="landing-card-strong rounded-2xl border border-white/10 bg-white/5 p-6">
                                    <h3 className={`text-lg font-semibold ${displayFontClassName}`}>{item.title}</h3>
                                    <p className="mt-3 text-sm text-gray-300">{item.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <section className="content-visibility-auto relative px-6 py-24">
                    <div className="mx-auto max-w-6xl text-center">
                        <div className="rounded-3xl border border-white/10 bg-black/70 p-6 backdrop-blur-md">
                            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Próximo passo</p>
                            <h2 className={`mt-4 text-3xl font-semibold sm:text-5xl ${displayFontClassName}`}>
                                Entre no futuro da agricultura hoje
                            </h2>
                            <p className="mx-auto mt-4 max-w-2xl text-base text-gray-300 sm:text-lg">
                                Teste grátis por 14 dias e descubra como a inteligência planetária transforma sua operação.
                            </p>
                            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                                <TrackLink
                                    href="/signup"
                                    goal="Signup Started"
                                    metadata={{ placement: 'final' }}
                                    className="min-h-touch min-w-touch rounded-full bg-blue-600 px-8 py-4 text-sm font-semibold uppercase tracking-wider transition-colors hover:bg-blue-500 cursor-pointer"
                                >
                                    Começar agora
                                </TrackLink>
                                <TrackLink
                                    href="/contact"
                                    goal="Demo Requested"
                                    metadata={{ placement: 'final' }}
                                    className="min-h-touch min-w-touch rounded-full border border-white/20 px-8 py-4 text-sm font-semibold uppercase tracking-wider text-white transition-colors hover:border-cyan-300 hover:text-cyan-300 cursor-pointer"
                                >
                                    Agendar demonstração
                                </TrackLink>
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="border-t border-white/10 bg-black/80 px-6 py-12">
                <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 text-sm text-gray-400 md:flex-row">
                    <div>© 2026 VivaCampo. Todos os direitos reservados.</div>
                    <div className="flex flex-wrap items-center justify-center gap-6">
                        <Link href="/login" className="inline-flex min-h-touch items-center transition-colors hover:text-cyan-300 cursor-pointer">Login</Link>
                        <Link href="/signup" className="inline-flex min-h-touch items-center transition-colors hover:text-cyan-300 cursor-pointer">Cadastro</Link>
                        <Link href="/terms" className="inline-flex min-h-touch items-center transition-colors hover:text-cyan-300 cursor-pointer">Termos</Link>
                        <Link href="/privacy" className="inline-flex min-h-touch items-center transition-colors hover:text-cyan-300 cursor-pointer">Privacidade</Link>
                        <Link href="/contact" className="inline-flex min-h-touch items-center transition-colors hover:text-cyan-300 cursor-pointer">Contato</Link>
                    </div>
                </div>
            </footer>
        </div>
    )
}
