'use client'

import Link from 'next/link'

export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
            <div className="mx-auto max-w-3xl px-6 py-16">
                <h1 className="text-3xl font-bold text-slate-900">Política de Privacidade</h1>
                <p className="mt-4 text-slate-600">
                    Esta Política de Privacidade descreve como coletamos, utilizamos e protegemos
                    os dados pessoais tratados na plataforma VivaCampo.
                </p>

                <div className="mt-8 space-y-6 text-sm text-slate-700">
                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">1. Dados Coletados</h2>
                        <p>
                            Coletamos informações necessárias para autenticação, gestão de contas e
                            prestação do serviço, incluindo nome, email e dados operacionais de uso.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">2. Uso dos Dados</h2>
                        <p>
                            Os dados são utilizados para operar a plataforma, melhorar a experiência
                            do usuário e cumprir obrigações legais.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">3. Compartilhamento</h2>
                        <p>
                            Não compartilhamos dados pessoais com terceiros sem base legal ou consentimento,
                            exceto quando necessário para prestação do serviço.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">4. Segurança</h2>
                        <p>
                            Implementamos medidas técnicas e organizacionais para proteger os dados.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">5. Direitos do Titular</h2>
                        <p>
                            Você pode solicitar acesso, correção ou exclusão de seus dados conforme a legislação.
                        </p>
                    </section>
                </div>

                <div className="mt-12">
                    <Link href="/signup" className="text-green-600 hover:text-green-700 font-semibold">
                        Voltar para cadastro
                    </Link>
                </div>
            </div>
        </div>
    )
}
