'use client'

import { useState, useEffect, useMemo } from 'react'
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { format, parseISO, subDays, isAfter } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface WeatherDataPoint {
    date: string
    temp_max: number
    temp_min: number
    precip_sum: number
    et0_fao: number
}

interface WeatherChartProps {
    data: WeatherDataPoint[]
}

type TimeRange = '7D' | '30D' | '90D'

export default function WeatherChart({ data }: WeatherChartProps) {
    const [timeRange, setTimeRange] = useState<TimeRange>('30D')
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
    }, [])

    const filteredData = useMemo(() => {
        if (!data || data.length === 0) return []

        const now = new Date()
        // Sort ascending
        const sorted = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

        const days = timeRange === '7D' ? 7 : timeRange === '30D' ? 30 : 90
        const cutoff = subDays(now, days)

        return sorted.filter(d => isAfter(parseISO(d.date), cutoff))
    }, [data, timeRange])

    if (!mounted) return <div className="h-64 w-full bg-gray-50 rounded-lg animate-pulse" />

    if (!data || data.length === 0) {
        return (
            <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-gray-500 text-sm">Sem dados meteorológicos disponíveis</p>
            </div>
        )
    }

    return (
        <div className="w-full bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Clima (Temp & Precipitação)</h4>

                <div className="flex bg-gray-100 p-0.5 rounded-lg">
                    {(['7D', '30D', '90D'] as TimeRange[]).map(range => (
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

            <div className="w-full" style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={filteredData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={(str) => format(parseISO(str), 'dd/MMM', { locale: ptBR })}
                            tick={{ fontSize: 10, fill: '#9ca3af' }}
                            stroke="#e5e7eb"
                        />
                        {/* Primary Axis: Temperature */}
                        <YAxis
                            yAxisId="left"
                            domain={['auto', 'auto']}
                            tick={{ fontSize: 10, fill: '#ef4444' }}
                            stroke="#e5e7eb"
                            label={{ value: '°C', position: 'insideTopLeft', fontSize: 10, fill: '#ef4444' }}
                        />
                        {/* Secondary Axis: Precip */}
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            domain={[0, 'auto']}
                            tick={{ fontSize: 10, fill: '#3b82f6' }}
                            stroke="#e5e7eb"
                            label={{ value: 'mm', position: 'insideTopRight', fontSize: 10, fill: '#3b82f6' }}
                        />
                        <Tooltip
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                            labelFormatter={(l) => format(parseISO(l), 'dd/MM/yyyy')}
                            formatter={(val: any, name: any) => {
                                if (name === 'temp_max') return [`${Number(val).toFixed(1)}°C`, 'Máxima']
                                if (name === 'temp_min') return [`${Number(val).toFixed(1)}°C`, 'Mínima']
                                if (name === 'precip_sum') return [`${Number(val).toFixed(1)} mm`, 'Chuva']
                                return [val, name]
                            }}
                        />
                        <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />

                        <Bar yAxisId="right" dataKey="precip_sum" fill="#93c5fd" barSize={20} name="Chuva" radius={[4, 4, 0, 0]} />
                        <Line yAxisId="left" type="monotone" dataKey="temp_max" stroke="#ef4444" strokeWidth={2} dot={false} name="Máxima" />
                        <Line yAxisId="left" type="monotone" dataKey="temp_min" stroke="#3b82f6" strokeWidth={2} dot={false} name="Mínima" />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}
