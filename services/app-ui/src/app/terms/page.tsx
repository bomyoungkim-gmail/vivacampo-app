'use client'

import Link from 'next/link'

export default function TermsPage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
            <main className="mx-auto max-w-3xl px-6 py-16">
                <h1 className="text-3xl font-bold text-slate-900">Termos de Uso</h1>
                <p className="mt-4 text-slate-700">
                    Estes Termos de Uso regulam o acesso e a utilização da plataforma VivaCampo.
                    Ao utilizar o serviço, você concorda com os termos descritos abaixo.
                </p>

                <div className="mt-8 space-y-6 text-sm text-slate-700">
                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">1. Aceitação</h2>
                        <p>
                            O uso da plataforma implica a aceitação integral destes Termos de Uso e
                            de quaisquer políticas complementares aplicáveis.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">2. Conta e Segurança</h2>
                        <p>
                            Você é responsável por manter a confidencialidade das credenciais de
                            acesso e por todas as atividades realizadas em sua conta.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">3. Uso Permitido</h2>
                        <p>
                            O serviço deve ser utilizado exclusivamente para fins lícitos e de acordo
                            com a legislação aplicável, incluindo normas de privacidade e proteção de dados.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">4. Limitações</h2>
                        <p>
                            A VivaCampo pode suspender contas que violem estes termos ou apresentem
                            risco para o funcionamento do serviço.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold text-slate-900">5. Atualizações</h2>
                        <p>
                            Estes termos podem ser atualizados periodicamente. A continuidade do uso
                            após alterações constitui aceitação dos novos termos.
                        </p>
                    </section>
                </div>

                <div className="mt-12">
                    <Link href="/signup" className="inline-flex min-h-touch items-center text-green-700 hover:text-green-800 font-semibold underline underline-offset-2">
                        Voltar para cadastro
                    </Link>
                </div>
            </main>
        </div>
    )
}
