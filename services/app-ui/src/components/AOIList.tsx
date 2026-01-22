'use client'

import { useState, useMemo } from 'react'
import { AOI, Signal } from '@/lib/types'
import { Search, Filter, AlertTriangle, Pencil, Trash2 } from 'lucide-react'

interface AOIListProps {
    aois: AOI[]
    selectedAOI: AOI | null
    onSelect: (aoi: AOI) => void
    processingAois: Set<string>
    signals?: Signal[]
    onAddAOI: () => void
    onEdit?: (aoi: AOI) => void
    onDelete?: (aoi: AOI) => void
}

export default function AOIList({
    aois,
    selectedAOI,
    onSelect,
    processingAois,
    signals = [],
    onAddAOI,
    onEdit,
    onDelete
}: AOIListProps) {
    const [searchTerm, setSearchTerm] = useState('')
    const [filterType, setFilterType] = useState<'ALL' | 'PASTURE' | 'CROP' | 'TIMBER'>('ALL')

    // Filter Logic
    const filteredAOIs = useMemo(() => {
        return aois.filter(aoi => {
            const matchesSearch = aoi.name.toLowerCase().includes(searchTerm.toLowerCase())
            const matchesType = filterType === 'ALL' || aoi.use_type === filterType
            return matchesSearch && matchesType
        })
    }, [aois, searchTerm, filterType])

    // Helper to get alerts count for an AOI
    const getAlertCount = (aoiId: string) => {
        return signals.filter(s => s.aoi_id === aoiId).length
    }

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
            {/* Header: Search & Filter */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 space-y-3">
                <div className="flex justify-between items-center">
                    <h2 className="font-bold text-gray-800 dark:text-gray-200 text-lg">Meus Talhões</h2>
                    <button
                        onClick={onAddAOI}
                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors shadow-sm"
                    >
                        + Novo
                    </button>
                </div>

                {/* Search Bar */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                    <input
                        type="text"
                        placeholder="Buscar por nome..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all placeholder-gray-400"
                    />
                </div>

                {/* Filter Chips */}
                <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
                    <button
                        onClick={() => setFilterType('ALL')}
                        className={`px-3 py-1 text-xs font-medium rounded-full transition-colors whitespace-nowrap ${filterType === 'ALL' ? 'bg-gray-800 text-white' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'}`}
                    >
                        Todos ({aois.length})
                    </button>
                    <button
                        onClick={() => setFilterType('PASTURE')}
                        className={`px-3 py-1 text-xs font-medium rounded-full transition-colors whitespace-nowrap ${filterType === 'PASTURE' ? 'bg-green-600 text-white' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}
                    >
                        Pastagem
                    </button>
                    <button
                        onClick={() => setFilterType('CROP')}
                        className={`px-3 py-1 text-xs font-medium rounded-full transition-colors whitespace-nowrap ${filterType === 'CROP' ? 'bg-orange-500 text-white' : 'bg-orange-100 text-orange-700 hover:bg-orange-200'}`}
                    >
                        Lavoura
                    </button>
                    <button
                        onClick={() => setFilterType('TIMBER')}
                        className={`px-3 py-1 text-xs font-medium rounded-full transition-colors whitespace-nowrap ${filterType === 'TIMBER' ? 'bg-[#8B4513] text-white' : 'bg-[#f4e4bc] text-[#5c2e0e] hover:bg-[#e3d0a3]'}`}
                    >
                        Madeira
                    </button>
                    {/* Add Alert filter later if needed */}
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {filteredAOIs.length === 0 ? (
                    <div className="text-center py-10 px-4">
                        <p className="text-gray-400 text-sm">Nenhum talhão encontrado.</p>
                        {searchTerm && <button onClick={() => setSearchTerm('')} className="text-green-600 text-xs font-bold mt-2 hover:underline">Limpar busca</button>}
                    </div>
                ) : (
                    filteredAOIs.map(aoi => {
                        const isSelected = selectedAOI?.id === aoi.id
                        const isProcessing = processingAois.has(aoi.id)
                        const alertCount = getAlertCount(aoi.id)

                        return (
                            <button
                                key={aoi.id}
                                onClick={() => onSelect(aoi)}
                                className={`w-full text-left p-3 rounded-lg border transition-all duration-200 group relative
                                    ${isSelected
                                        ? 'border-green-500 bg-green-50 dark:bg-green-900/20 shadow-sm ring-1 ring-green-500 z-10'
                                        : 'border-gray-100 dark:border-gray-700 hover:border-green-300 dark:hover:border-green-700 bg-white dark:bg-gray-800'
                                    }
                                `}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <span className="font-semibold text-sm text-gray-800 dark:text-gray-200 truncate pr-2">
                                        {aoi.name}
                                    </span>
                                    {alertCount > 0 && (
                                        <span className="flex items-center gap-1 text-[10px] font-bold text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded-full">
                                            <AlertTriangle size={10} /> {alertCount}
                                        </span>
                                    )}
                                </div>

                                <div className="flex items-center justify-between mt-2">
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wide
                                        ${aoi.use_type === 'CROP' ? 'bg-orange-50 text-orange-600'
                                            : aoi.use_type === 'TIMBER' ? 'bg-[#f4e4bc] text-[#8B4513]'
                                                : 'bg-green-50 text-green-600'}
                                    `}>
                                        {aoi.use_type === 'PASTURE' ? 'Pastagem' : aoi.use_type === 'TIMBER' ? 'Madeira' : 'Lavoura'}
                                    </span>

                                    <div className="flex items-center gap-2">
                                        {isProcessing && (
                                            <span className="text-[10px] text-amber-500 font-medium animate-pulse">
                                                Processando...
                                            </span>
                                        )}
                                        <span className="text-xs text-gray-400 font-medium">
                                            {aoi.area_ha ? `${aoi.area_ha.toFixed(1)} ha` : '--'}
                                        </span>
                                    </div>
                                </div>

                                {/* Simple Sparkline Placeholder (Can be replaced with real chart later) */}
                                {!isProcessing && (
                                    <div className="h-1 w-full bg-gray-100 rounded-full mt-3 overflow-hidden">
                                        <div className="h-full bg-green-500 w-[70%] opacity-20"></div> {/* Dummy visualization */}
                                    </div>
                                )}

                                {/* Action Buttons (Hover Only) */}
                                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white dark:bg-gray-800 rounded-md shadow-sm border border-gray-200 dark:border-gray-700 p-0.5">
                                    {onEdit && (
                                        <div
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                onEdit(aoi)
                                            }}
                                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                            title="Editar geometria"
                                        >
                                            <Pencil size={14} />
                                        </div>
                                    )}
                                    {onDelete && (
                                        <div
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                onDelete(aoi)
                                            }}
                                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                            title="Excluir talhão"
                                        >
                                            <Trash2 size={14} />
                                        </div>
                                    )}
                                </div>
                            </button>
                        )
                    })
                )}
            </div >
        </div >
    )
}
