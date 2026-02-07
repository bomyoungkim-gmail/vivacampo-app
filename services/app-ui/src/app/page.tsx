'use client'

import Link from 'next/link'
import { Poppins, Open_Sans } from 'next/font/google'

const poppins = Poppins({ subsets: ['latin'], weight: ['400', '500', '600', '700'] })
const openSans = Open_Sans({ subsets: ['latin'], weight: ['400', '500', '600'] })

export default function LandingPage() {
    return (
        <div className={`min-h-screen bg-[#EFF6FF] text-[#1E3A8A] ${openSans.className}`}>
            <nav className="fixed top-4 left-4 right-4 z-50 rounded-2xl border border-gray-200 bg-white/80 shadow-lg backdrop-blur-lg">
                <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
                    <div className="flex items-center gap-2">
                        <svg className="h-8 w-8 text-green-600" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
                        </svg>
                        <span className={`text-xl font-semibold text-slate-900 ${poppins.className}`}>VivaCampo</span>
                    </div>
                    <div className="hidden items-center gap-8 md:flex">
                        <a href="#features" className="text-slate-600 transition-colors hover:text-slate-900 cursor-pointer">Recursos</a>
                        <a href="#pricing" className="text-slate-600 transition-colors hover:text-slate-900 cursor-pointer">Preços</a>
                        <a href="#contact" className="text-slate-600 transition-colors hover:text-slate-900 cursor-pointer">Contato</a>
                        <Link href="/login" className="text-slate-600 transition-colors hover:text-slate-900 cursor-pointer">Login</Link>
                        <Link href="/signup" className="rounded-lg bg-green-600 px-6 py-2 text-white transition-colors hover:bg-green-700 cursor-pointer">Começar Grátis</Link>
                    </div>
                </div>
            </nav>

            <section className="px-4 pb-20 pt-32">
                <div className="mx-auto grid max-w-7xl items-center gap-12 md:grid-cols-2">
                    <div>
                        <h1 className={`mb-6 text-4xl font-bold text-slate-900 md:text-6xl ${poppins.className}`}>
                            Inteligência Agrícola via
                            <span className="text-green-600"> Satélite</span>
                        </h1>
                        <p className="mb-8 text-lg text-slate-600 md:text-xl">
                            Monitore lavouras em tempo real com índices de vegetação, alertas personalizados e
                            análises históricas. Tome decisões rápidas com dados confiáveis.
                        </p>
                        <div className="flex flex-col gap-4 sm:flex-row">
                            <Link href="/signup" className="rounded-lg bg-green-600 px-8 py-4 text-center text-lg font-semibold text-white transition-colors hover:bg-green-700 cursor-pointer">
                                Começar Grátis
                            </Link>
                            <a href="#features" className="rounded-lg border-2 border-slate-200 bg-white px-8 py-4 text-center text-lg font-semibold text-slate-900 transition-colors hover:border-slate-300 cursor-pointer">
                                Ver Recursos
                            </a>
                        </div>
                        <div className="mt-8 flex items-center gap-6">
                            <div>
                                <div className="flex items-center gap-1">
                                    {[...Array(5)].map((_, i) => (
                                        <svg
                                            key={i}
                                            className="h-5 w-5 text-yellow-400"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                        </svg>
                                    ))}
                                </div>
                                <p className="mt-1 text-sm text-slate-600">4.9/5 de 500+ agricultores</p>
                            </div>
                        </div>
                    </div>

                    <div className="relative">
                        <div className="rounded-2xl border border-gray-200 bg-white/80 p-6 shadow-2xl backdrop-blur-lg">
                            <div className="aspect-video rounded-lg bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
                                <svg className="h-24 w-24 text-green-600" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
                                </svg>
                            </div>
                            <div className="mt-6 grid grid-cols-3 gap-4">
                                <div className="rounded-lg border border-gray-200 bg-white p-4">
                                    <p className="text-2xl font-bold text-green-600">0.75</p>
                                    <p className="text-xs text-slate-600">NDVI Médio</p>
                                </div>
                                <div className="rounded-lg border border-gray-200 bg-white p-4">
                                    <p className="text-2xl font-bold text-blue-600">12</p>
                                    <p className="text-xs text-slate-600">Talhões</p>
                                </div>
                                <div className="rounded-lg border border-gray-200 bg-white p-4">
                                    <p className="text-2xl font-bold text-orange-600">3</p>
                                    <p className="text-xs text-slate-600">Alertas</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section id="features" className="bg-white px-4 py-20">
                <div className="mx-auto max-w-7xl">
                    <div className="mb-16 text-center">
                        <h2 className={`mb-4 text-4xl font-bold text-slate-900 md:text-5xl ${poppins.className}`}>
                            Recursos Poderosos
                        </h2>
                        <p className="mx-auto max-w-3xl text-xl text-slate-600">
                            Tudo que você precisa para monitorar e otimizar suas lavouras em uma única plataforma
                        </p>
                    </div>

                    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                        {[
                            {
                                title: 'Monitoramento por Satélite',
                                description: 'Imagens semanais com resolução de 10m para acompanhar o desenvolvimento das lavouras sem sair do campo.',
                            },
                            {
                                title: 'Índices de Vegetação',
                                description: 'NDVI, NDWI, SAVI e mais para detectar estresse hídrico e nutricional de forma precoce.',
                            },
                            {
                                title: 'Alertas Personalizados',
                                description: 'Regras visuais para notificar riscos de produtividade e orientar ações imediatas.',
                            },
                            {
                                title: 'Histórico Completo',
                                description: 'Séries temporais desde 2020 com análises de tendências e comparação de safras.',
                            },
                            {
                                title: 'Análise de Custos',
                                description: 'Integre dados de insumos e descubra áreas com melhor ROI.',
                            },
                            {
                                title: 'Multi-Tenant',
                                description: 'Gestão de múltiplos usuários e fazendas com níveis de permissão claros.',
                            },
                        ].map((feature) => (
                            <div
                                key={feature.title}
                                className="rounded-xl border border-gray-200 bg-white p-8 transition-shadow hover:shadow-lg cursor-pointer"
                            >
                                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 text-green-600">
                                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6l4 2" />
                                    </svg>
                                </div>
                                <h3 className={`mb-3 text-xl font-semibold text-slate-900 ${poppins.className}`}>
                                    {feature.title}
                                </h3>
                                <p className="text-slate-600">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <section id="pricing" className="bg-gradient-to-b from-white to-blue-50 px-4 py-20">
                <div className="mx-auto max-w-7xl">
                    <div className="mb-16 text-center">
                        <h2 className={`mb-4 text-4xl font-bold text-slate-900 md:text-5xl ${poppins.className}`}>
                            Planos para cada operação
                        </h2>
                        <p className="text-xl text-slate-600">Escolha o plano ideal para seu estágio de crescimento.</p>
                    </div>

                    <div className="grid gap-8 lg:grid-cols-3">
                        {[
                            {
                                name: 'Free',
                                price: 'R$ 0',
                                description: 'Perfeito para começar',
                                features: ['1 fazenda', '3 talhões', 'Imagens semanais', 'NDVI e NDWI', 'Histórico de 3 meses'],
                                cta: 'Começar Grátis',
                                highlighted: false,
                            },
                            {
                                name: 'Professional',
                                price: 'R$ 199',
                                description: 'Para agricultores profissionais',
                                features: ['5 fazendas', '50 talhões', 'Imagens a cada 3 dias', 'Todos os índices', 'Alertas ilimitados', 'Histórico completo'],
                                cta: 'Assinar Professional',
                                highlighted: true,
                            },
                            {
                                name: 'Enterprise',
                                price: 'Customizado',
                                description: 'Para cooperativas e consultorias',
                                features: ['Fazendas ilimitadas', 'Talhões ilimitados', 'Multi-tenant', 'API dedicada', 'Imagens diárias', 'White-label'],
                                cta: 'Falar com Vendas',
                                highlighted: false,
                            },
                        ].map((plan) => (
                            <div
                                key={plan.name}
                                className={`rounded-2xl border ${plan.highlighted ? 'border-green-600 shadow-2xl' : 'border-gray-200'} bg-white p-8`}
                            >
                                <h3 className={`text-2xl font-semibold text-slate-900 ${poppins.className}`}>{plan.name}</h3>
                                <p className="mt-2 text-sm text-slate-600">{plan.description}</p>
                                <div className="mt-6 flex items-end gap-2">
                                    <span className={`text-4xl font-bold text-slate-900 ${poppins.className}`}>{plan.price}</span>
                                    <span className="text-sm text-slate-600">/mês</span>
                                </div>
                                <ul className="mt-6 space-y-2 text-sm text-slate-600">
                                    {plan.features.map((feature) => (
                                        <li key={feature} className="flex items-start gap-2">
                                            <span className="mt-1 h-2 w-2 rounded-full bg-green-600"></span>
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                                <Link
                                    href={plan.name === 'Enterprise' ? '/contact' : '/signup'}
                                    className={`mt-8 block rounded-lg px-6 py-3 text-center font-semibold transition-colors cursor-pointer ${
                                        plan.highlighted
                                            ? 'bg-green-600 text-white hover:bg-green-700'
                                            : 'border border-gray-200 text-slate-900 hover:border-slate-300'
                                    }`}
                                >
                                    {plan.cta}
                                </Link>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <section className="bg-white px-4 py-20">
                <div className="mx-auto max-w-7xl">
                    <div className="mb-16 text-center">
                        <h2 className={`mb-4 text-4xl font-bold text-slate-900 md:text-5xl ${poppins.className}`}>
                            Agricultores que confiam
                        </h2>
                        <p className="text-xl text-slate-600">Resultados reais em propriedades de diferentes portes.</p>
                    </div>

                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                name: 'Fazenda Santa Maria',
                                quote: 'Reduzimos perdas em 18% com alertas de estresse hídrico em tempo real.',
                            },
                            {
                                name: 'Cooperativa Vale Verde',
                                quote: 'Agora conseguimos acompanhar 120 talhões sem depender de visitas semanais.',
                            },
                            {
                                name: 'AgroConsult',
                                quote: 'Os relatórios automáticos aceleraram a tomada de decisão com os clientes.',
                            },
                        ].map((item) => (
                            <div key={item.name} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                                <p className="text-slate-600">“{item.quote}”</p>
                                <p className={`mt-4 text-sm font-semibold text-slate-900 ${poppins.className}`}>{item.name}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <section id="contact" className="bg-[#EFF6FF] px-4 py-20">
                <div className="mx-auto max-w-5xl text-center">
                    <h2 className={`mb-4 text-4xl font-bold text-slate-900 md:text-5xl ${poppins.className}`}>
                        Vamos conversar
                    </h2>
                    <p className="mx-auto mb-10 max-w-2xl text-xl text-slate-600">
                        Fale com nossa equipe para entender como aplicar a inteligência geoespacial na sua operação.
                    </p>
                    <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
                        <Link href="/contact" className="rounded-lg bg-green-600 px-8 py-4 text-lg font-semibold text-white transition-colors hover:bg-green-700 cursor-pointer">
                            Falar com especialista
                        </Link>
                        <Link href="/signup" className="rounded-lg border-2 border-slate-200 bg-white px-8 py-4 text-lg font-semibold text-slate-900 transition-colors hover:border-slate-300 cursor-pointer">
                            Criar conta grátis
                        </Link>
                    </div>
                </div>
            </section>

            <footer className="bg-white px-4 py-12">
                <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 md:flex-row">
                    <div className="text-sm text-slate-600">© 2026 VivaCampo. Todos os direitos reservados.</div>
                    <div className="flex items-center gap-6 text-sm text-slate-600">
                        <Link href="/login" className="hover:text-slate-900 cursor-pointer">Login</Link>
                        <Link href="/signup" className="hover:text-slate-900 cursor-pointer">Cadastro</Link>
                        <Link href="/terms" className="hover:text-slate-900 cursor-pointer">Termos</Link>
                        <Link href="/privacy" className="hover:text-slate-900 cursor-pointer">Privacidade</Link>
                        <Link href="/contact" className="hover:text-slate-900 cursor-pointer">Contato</Link>
                    </div>
                </div>
            </footer>
        </div>
    )
}
