'use client'

import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ChartData {
    date: string
    ndvi?: number
    score?: number
}

interface ChartProps {
    data: ChartData[]
}

export function NDVIChart({ data }: ChartProps) {
    if (!data || data.length === 0) {
        return (
            <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow">
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">NDVI Timeline</h3>
                <div className="flex h-64 items-center justify-center text-gray-500 dark:text-gray-400">
                    Sem dados disponíveis
                </div>
            </div>
        )
    }

    return (
        <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow">
            <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">NDVI Timeline</h3>
            <div className="aspect-[16/9] w-full max-h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' })}
                        />
                        <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
                        <Tooltip
                            labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                            formatter={(value) => (value as number)?.toFixed(3) || '0.000'}
                        />
                        <Legend />
                        <Area
                            type="monotone"
                            dataKey="ndvi"
                            stroke="#10b981"
                            fill="#10b981"
                            fillOpacity={0.3}
                            name="NDVI"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export function SignalScoreChart({ data }: ChartProps) {
    if (!data || data.length === 0) {
        return (
            <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow">
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Signal Score</h3>
                <div className="flex h-64 items-center justify-center text-gray-500 dark:text-gray-400">
                    Sem dados disponíveis
                </div>
            </div>
        )
    }

    return (
        <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow">
            <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Signal Score</h3>
            <div className="aspect-[16/9] w-full max-h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' })}
                        />
                        <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
                        <Tooltip
                            labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                            formatter={(value) => (value as number)?.toFixed(3) || '0.000'}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="score"
                            stroke="#f59e0b"
                            strokeWidth={2}
                            dot={{ r: 4 }}
                            name="Score"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}
