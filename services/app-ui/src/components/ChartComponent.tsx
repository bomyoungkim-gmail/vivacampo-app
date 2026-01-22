'use client'

import { useState, useEffect, useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { format, parseISO, subDays, isAfter } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface ChartComponentProps {
    data: { date: string; value: number }[]
    title: string
    color?: string
    domain?: [number, number] | ['auto', 'auto']
}

type TimeRange = '7D' | '30D' | '90D' | 'SAFRA'

export default function ChartComponent({ data, title, color = '#10b981', domain = [0, 1] }: ChartComponentProps) {
    const [timeRange, setTimeRange] = useState<TimeRange>('30D')
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
    }, [])

    // Filter Logic
    const filteredData = useMemo(() => {
        if (!data || data.length === 0) return []

        const now = new Date()
        const sorted = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

        if (timeRange === 'SAFRA') return sorted // Return all available history for Safra

        const days = timeRange === '7D' ? 7 : timeRange === '30D' ? 30 : 90
        const cutoff = subDays(now, days)

        return sorted.filter(d => isAfter(parseISO(d.date), cutoff))
    }, [data, timeRange])

    // Metrics Calculation
    const { lastValue, variation, trend } = useMemo(() => {
        if (filteredData.length === 0) return { lastValue: null, variation: null, trend: 'neutral' }

        const last = filteredData[filteredData.length - 1].value
        const first = filteredData[0].value

        const diff = last - first
        const pct = first !== 0 ? (diff / first) * 100 : 0

        return {
            lastValue: last,
            variation: pct,
            trend: diff > 0 ? 'up' : diff < 0 ? 'down' : 'neutral'
        }
    }, [filteredData])

    if (!mounted) return <div className="h-64 w-full bg-gray-50 rounded-lg animate-pulse" />

    if (!data || data.length === 0) {
        return (
            <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-gray-500 text-sm">Sem dados históricos disponíveis</p>
            </div>
        )
    }

    return (
        <div className="w-full bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            {/* Header with Metrics */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{title}</h4>
                    <div className="flex items-baseline gap-3">
                        <span className="text-2xl font-bold text-gray-900">
                            {lastValue !== null ? lastValue.toFixed(2) : '--'}
                        </span>
                        {variation !== null && (
                            <span className={`text-sm font-medium flex items-center ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
                                {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '•'} {Math.abs(variation).toFixed(1)}%
                                <span className="text-gray-400 font-normal ml-1">vs início</span>
                            </span>
                        )}
                    </div>
                </div>

                {/* Range Filters */}
                <div className="flex bg-gray-100 p-0.5 rounded-lg">
                    {(['7D', '30D', '90D', 'SAFRA'] as TimeRange[]).map(range => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range)}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${timeRange === range
                                ? 'bg-white text-gray-900 shadow-sm'
                                : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart Area */}
            <div className="w-full" style={{ height: '240px' }}>
                {filteredData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={filteredData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                            <XAxis
                                dataKey="date"
                                tickFormatter={(str) => format(parseISO(str), 'dd/MMM', { locale: ptBR })}
                                tick={{ fontSize: 10, fill: '#9ca3af' }}
                                stroke="#e5e7eb"
                                minTickGap={30}
                            />
                            <YAxis
                                domain={domain}
                                tick={{ fontSize: 10, fill: '#9ca3af' }}
                                stroke="#e5e7eb"
                                tickFormatter={(val) => val.toFixed(1)}
                            />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                                labelFormatter={(label) => format(parseISO(label), 'dd ' + (isAfter(parseISO(label), new Date().setFullYear(new Date().getFullYear() - 1)) ? 'MMMM' : 'MMM yyyy'), { locale: ptBR })}
                                formatter={(value: number | undefined) => [value?.toFixed(2) ?? '--', title]}
                            />
                            <ReferenceLine y={0.3} label={{ value: 'Solo', position: 'insideLeft', fontSize: 10, fill: '#ef4444' }} stroke="#fca5a5" strokeDasharray="3 3" />
                            <ReferenceLine y={0.8} label={{ value: 'Vigor', position: 'insideLeft', fontSize: 10, fill: '#22c55e' }} stroke="#86efac" strokeDasharray="3 3" />
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke={color}
                                strokeWidth={2.5}
                                dot={false}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                                connectNulls={false} // Don't bridge gaps, show them
                                animationDuration={500}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                        Sem dados neste período
                    </div>
                )}
            </div>
        </div>
    )
}
