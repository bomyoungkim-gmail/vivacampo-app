'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { aiAssistantAPI } from '@/lib/api'
import { useAuthProtection } from '@/lib/auth'
import { useErrorHandler } from '@/lib/errorHandler'
import { ErrorToast } from '@/components/Toast'
import MobileNav from '@/components/MobileNav'

export default function AIAssistantPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const [threads, setThreads] = useState<any[]>([])
    const [activeThread, setActiveThread] = useState<any>(null)
    const [messages, setMessages] = useState<any[]>([])
    const [newMessage, setNewMessage] = useState('')
    const [loading, setLoading] = useState(true)
    const [sending, setSending] = useState(false)
    const [showSidebar, setShowSidebar] = useState(false)

    // Error Handling
    const { error, handleError, clearError } = useErrorHandler()

    useEffect(() => {
        if (isAuthenticated) {
            loadThreads()
        }
    }, [isAuthenticated])

    const loadThreads = async () => {
        try {
            const response = await aiAssistantAPI.listThreads()
            setThreads(response.data)
            if (response.data.length > 0) {
                selectThread(response.data[0])
            }
        } catch (err) {
            console.error('Failed to load threads:', err)
            handleError(err, 'Falha ao carregar conversas')
        } finally {
            setLoading(false)
        }
    }

    const selectThread = async (thread: any) => {
        setActiveThread(thread)
        try {
            const response = await aiAssistantAPI.getMessages(thread.id)
            setMessages(response.data)
        } catch (err) {
            console.error('Failed to load messages:', err)
            handleError(err, 'Falha ao carregar mensagens')
        }
    }

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!newMessage.trim() || !activeThread) return

        setSending(true)
        try {
            await aiAssistantAPI.sendMessage(activeThread.id, {
                message: newMessage
            })
            setNewMessage('')
            // Reload messages
            const response = await aiAssistantAPI.getMessages(activeThread.id)
            setMessages(response.data)
        } catch (err: any) {
            handleError(err, 'Erro ao enviar mensagem')
        } finally {
            setSending(false)
        }
    }

    const handleCreateThread = async () => {
        const signalId = prompt('Digite o ID do sinal (opcional):')
        try {
            await aiAssistantAPI.createThread({
                signal_id: signalId || null,
                initial_message: 'Olá, preciso de ajuda'
            })
            loadThreads()
        } catch (err: any) {
            handleError(err, 'Erro ao criar thread')
        }
    }

    if (authLoading || loading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
                    <p className="mt-2 text-gray-600">Carregando...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col lg:flex-row h-screen bg-gray-50">
            {/* Toast Notifications */}
            <ErrorToast error={error} onClose={clearError} />

            {/* Mobile Header */}
            <div className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between">
                <button
                    onClick={() => setShowSidebar(!showSidebar)}
                    className="p-2 text-gray-600 hover:text-gray-900 min-h-touch min-w-touch"
                >
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
                <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
                <button
                    onClick={handleCreateThread}
                    className="p-2 text-green-600 hover:text-green-700 min-h-touch min-w-touch"
                >
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                </button>
            </div>

            {/* Sidebar - Threads List (Mobile: Overlay, Desktop: Fixed) */}
            {showSidebar && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
                    onClick={() => setShowSidebar(false)}
                />
            )}
            <div className={`
                fixed lg:relative inset-y-0 left-0 z-50 lg:z-0
                w-80 lg:w-80 transform transition-transform duration-300 ease-in-out
                ${showSidebar ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                border-r border-gray-200 bg-white flex flex-col
            `}>
                <div className="border-b border-gray-200 p-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-gray-900 hidden lg:block">AI Assistant</h2>
                        <button
                            onClick={() => setShowSidebar(false)}
                            className="lg:hidden p-2 text-gray-600 hover:text-gray-900 min-h-touch min-w-touch"
                        >
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <Link href="/dashboard" className="hidden lg:inline-flex min-h-touch items-center text-sm text-gray-600 hover:text-gray-900">
                            ← Dashboard
                        </Link>
                    </div>
                    <button
                        onClick={handleCreateThread}
                        className="mt-4 w-full rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 min-h-touch hidden lg:block"
                    >
                        + Nova Conversa
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {loading ? (
                        <div className="p-4 text-center">
                            <div className="inline-block h-6 w-6 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
                        </div>
                    ) : threads.length === 0 ? (
                        <div className="p-4 text-center text-sm text-gray-500">
                            Nenhuma conversa ainda
                        </div>
                    ) : (
                        threads.map((thread) => (
                            <button
                                key={thread.id}
                                onClick={() => {
                                    selectThread(thread)
                                    setShowSidebar(false)
                                }}
                                className={`w-full border-b border-gray-200 p-4 text-left hover:bg-gray-50 min-h-touch ${activeThread?.id === thread.id ? 'bg-green-50' : ''
                                    }`}
                            >
                                <p className="text-sm font-medium text-gray-900">
                                    Thread {thread.id.substring(0, 8)}
                                </p>
                                <p className="mt-1 text-xs text-gray-600">
                                    {new Date(thread.created_at).toLocaleDateString('pt-BR')}
                                </p>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex flex-1 flex-col h-full pb-16 lg:pb-0">
                {activeThread ? (
                    <>
                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
                            {messages.length === 0 ? (
                                <div className="flex h-full items-center justify-center text-gray-500 text-sm">
                                    Nenhuma mensagem ainda
                                </div>
                            ) : (
                                <div className="space-y-3 sm:space-y-4">
                                    {messages.map((message, index) => (
                                        <div
                                            key={index}
                                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                        >
                                            <div
                                                className={`max-w-[85%] sm:max-w-2xl rounded-lg px-3 sm:px-4 py-2 sm:py-3 ${message.role === 'user'
                                                    ? 'bg-green-600 text-white'
                                                    : 'bg-white text-gray-900 shadow'
                                                    }`}
                                            >
                                                <p className="text-xs sm:text-sm">{message.content}</p>
                                                <p className="mt-1 text-xs opacity-75">
                                                    {new Date(message.created_at).toLocaleTimeString('pt-BR')}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Input */}
                        <div className="border-t border-gray-200 bg-white p-3 sm:p-4">
                            <form onSubmit={handleSendMessage} className="flex gap-2 sm:gap-3">
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    placeholder="Digite sua mensagem..."
                                    autoComplete="off"
                                    className="flex-1 rounded-lg border border-gray-300 px-3 sm:px-4 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-green-500 min-h-touch"
                                    disabled={sending}
                                />
                                <button
                                    type="submit"
                                    disabled={sending || !newMessage.trim()}
                                    className="rounded-lg bg-green-600 px-4 sm:px-6 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50 min-h-touch"
                                >
                                    {sending ? '...' : 'Enviar'}
                                </button>
                            </form>
                        </div>
                    </>
                ) : (
                    <div className="flex h-full items-center justify-center text-gray-500 text-sm p-4">
                        {threads.length === 0 ? 'Crie uma nova conversa para começar' : 'Selecione uma conversa'}
                    </div>
                )}
            </div>

            {/* Mobile Navigation */}
            <MobileNav />
        </div>
    )
}
