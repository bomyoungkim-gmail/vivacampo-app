/**
 * Empty State Components
 * Provide clear, friendly feedback when there's no data
 * More intuitive than plain text - guides users on what to do next
 */

interface EmptyStateProps {
    icon?: React.ReactNode
    title: string
    description: string
    action?: {
        label: string
        onClick: () => void
    }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <div className="rounded-lg bg-white p-8 sm:p-12 text-center shadow">
            {icon && (
                <div className="mx-auto w-16 h-16 sm:w-20 sm:h-20 mb-4 text-gray-400">
                    {icon}
                </div>
            )}
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">{title}</h3>
            <p className="text-sm sm:text-base text-gray-600 mb-6 max-w-md mx-auto">{description}</p>
            {action && (
                <button
                    onClick={action.onClick}
                    className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 sm:px-6 py-2 sm:py-3 text-sm font-semibold text-white hover:bg-green-700 transition-colors min-h-touch"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {action.label}
                </button>
            )}
        </div>
    )
}

export function EmptyFarms({ onCreate }: { onCreate: () => void }) {
    return (
        <EmptyState
            icon={
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            }
            title="Nenhuma fazenda cadastrada"
            description="Comece criando sua primeira fazenda para monitorar suas áreas agrícolas via satélite."
            action={{
                label: "Criar primeira fazenda",
                onClick: onCreate
            }}
        />
    )
}

export function EmptySignals() {
    return (
        <EmptyState
            icon={
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            }
            title="Nenhum sinal detectado"
            description="Os sinais aparecerão aqui quando anomalias forem detectadas nas suas áreas monitoradas."
        />
    )
}

export function EmptyThreads({ onCreate }: { onCreate: () => void }) {
    return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            <div className="w-16 h-16 mb-4 text-gray-400">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
            </div>
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Nenhuma conversa ainda</h3>
            <p className="text-sm text-gray-600 mb-6 max-w-xs">
                Converse com a IA para obter insights sobre suas fazendas e sinais detectados.
            </p>
            <button
                onClick={onCreate}
                className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-6 py-3 text-sm font-semibold text-white hover:bg-green-700 transition-colors min-h-touch lg:hidden"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Iniciar conversa
            </button>
        </div>
    )
}

export function EmptyMessages() {
    return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center text-gray-500">
            <div className="w-12 h-12 mb-3 text-gray-300">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
            </div>
            <p className="text-sm">Digite uma mensagem para começar a conversa</p>
        </div>
    )
}

export function EmptyAOIs() {
    return (
        <div className="p-8 text-center text-gray-500">
            <div className="w-12 h-12 mx-auto mb-3 text-gray-300">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
            </div>
            <p className="text-sm font-medium mb-1">Nenhum talhão cadastrado</p>
            <p className="text-xs">Desenhe seus talhões no mapa ao lado</p>
        </div>
    )
}
