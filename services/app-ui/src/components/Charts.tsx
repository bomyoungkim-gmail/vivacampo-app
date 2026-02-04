'use client'

import { Cloud } from 'lucide-react'
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    TooltipProps,
} from 'recharts'
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent'

interface ChartData {
    date: string
    ndvi?: number
    rvi?: number
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
                            content={<RadarFallbackTooltip />}
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
                            connectNulls={false}
                            dot={({ cx, cy, payload }) => {
                                if (cx == null || cy == null) return null
                                const point = payload as ChartData
                                if (point.ndvi == null && point.rvi != null) {
                                    return (
                                        <circle
                                            cx={cx}
                                            cy={cy}
                                            r={4}
                                            fill="none"
                                            stroke="#10b981"
                                            strokeWidth={2}
                                        />
                                    )
                                }
                                return <circle cx={cx} cy={cy} r={3} fill="#10b981" />
                            }}
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

function RadarFallbackTooltip({ active, payload, label }: TooltipProps<ValueType, NameType>) {
    if (!active || !payload || payload.length === 0) {
        return null
    }

    const point = payload[0]?.payload as ChartData | undefined
    if (!point) {
        return null
    }

    if (point.ndvi == null && point.rvi != null) {
        return (
            <div className="rounded-lg border bg-background p-3 shadow-lg">
                <div className="mb-2 flex items-center gap-2">
                    <Cloud className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">Dia Nublado</span>
                </div>
                <p className="text-sm text-muted-foreground">Dado óptico indisponível.</p>
                <p className="text-sm">
                    Estimativa via Sentinel-1: <span className="font-mono">{point.rvi.toFixed(2)}</span>
                </p>
            </div>
        )
    }

    const formattedDate = label ? new Date(label as string).toLocaleDateString('pt-BR') : ''

    return (
        <div className="rounded-lg border bg-background p-3 shadow-lg">
            <p className="text-sm font-medium">{formattedDate}</p>
            <p className="text-sm">NDVI: {point.ndvi != null ? point.ndvi.toFixed(3) : 'N/A'}</p>
        </div>
    )
}
