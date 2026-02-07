'use client'

import Link from 'next/link'
import { Poppins, Open_Sans } from 'next/font/google'

const poppins = Poppins({ subsets: ['latin'], weight: ['400', '500', '600', '700'] })
const openSans = Open_Sans({ subsets: ['latin'], weight: ['400', '500', '600'] })

export default function ContactPage() {
    return (
        <div className={`min-h-screen bg-[#EFF6FF] text-[#1E3A8A] ${openSans.className}`}>
            <div className="mx-auto max-w-3xl px-6 py-16">
                <h1 className={`text-3xl font-bold text-slate-900 ${poppins.className}`}>Fale com a VivaCampo</h1>
                <p className="mt-4 text-slate-600">
                    Compartilhe o tamanho da sua operação e nossos especialistas vão indicar o melhor plano.
                </p>

                <form className="mt-10 space-y-6 rounded-2xl border border-gray-200 bg-white p-8 shadow-lg">
                    <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700">Nome</label>
                        <input
                            id="name"
                            type="text"
                            required
                            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                            placeholder="Seu nome"
                        />
                    </div>

                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                        <input
                            id="email"
                            type="email"
                            required
                            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                            placeholder="seu@email.com"
                        />
                    </div>

                    <div>
                        <label htmlFor="company" className="block text-sm font-medium text-gray-700">Fazenda/Empresa</label>
                        <input
                            id="company"
                            type="text"
                            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                            placeholder="Nome da fazenda"
                        />
                    </div>

                    <div>
                        <label htmlFor="message" className="block text-sm font-medium text-gray-700">Mensagem</label>
                        <textarea
                            id="message"
                            rows={4}
                            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                            placeholder="Conte sobre seus desafios"
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full rounded-lg bg-green-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-green-700 cursor-pointer"
                    >
                        Enviar mensagem
                    </button>
                </form>

                <div className="mt-8 text-sm text-slate-600">
                    Ou fale direto pelo email: <span className="font-semibold text-slate-900">contato@vivacampo.com</span>
                </div>

                <div className="mt-8">
                    <Link href="/" className="text-green-600 hover:text-green-700 font-semibold">
                        Voltar para a landing page
                    </Link>
                </div>
            </div>
        </div>
    )
}
