'use client'

import { useState, useRef, useEffect } from 'react'
import { MoreVertical, Edit2, Copy, Download, Trash2 } from 'lucide-react'

interface AOIActionsMenuProps {
    onEditGeometry?: () => void
    onEditData?: () => void
    onDuplicate?: () => void
    onExport?: () => void
    onDelete?: () => void
    isOpen?: boolean // Can be controlled or uncontrolled
}

export default function AOIActionsMenu({
    onEditGeometry,
    onEditData,
    onDuplicate,
    onExport,
    onDelete
}: AOIActionsMenuProps) {
    const [isOpen, setIsOpen] = useState(false)
    const menuRef = useRef<HTMLDivElement>(null)

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside)
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [isOpen])

    return (
        <div className="relative" ref={menuRef}>
            <button
                onClick={(e) => {
                    e.stopPropagation()
                    setIsOpen(!isOpen)
                }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                title="Ações do Talhão"
            >
                <MoreVertical size={20} />
            </button>

            {isOpen && (
                <div
                    className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-[9999] overflow-hidden animate-in fade-in zoom-in-95 duration-100 origin-top-right"
                    onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
                >
                    <div className="py-1">
                        {onEditGeometry && (
                            <button
                                onClick={() => { setIsOpen(false); onEditGeometry() }}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-green-600 transition-colors text-left"
                            >
                                <Edit2 size={16} />
                                Editar Geometria
                            </button>
                        )}
                        {/* 
                        {onEditData && (
                            <button
                                onClick={() => { setIsOpen(false); onEditData() }}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-green-600 transition-colors text-left"
                            >
                                <FileEdit size={16} />
                                Editar Dados
                            </button>
                        )} 
                        */}
                        {onDuplicate && (
                            <button
                                onClick={() => { setIsOpen(false); onDuplicate() }}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors text-left"
                            >
                                <Copy size={16} />
                                Duplicar
                            </button>
                        )}

                        {(onEditGeometry || onDuplicate) && <div className="border-t border-gray-100 my-1"></div>}

                        {onExport && (
                            <button
                                onClick={() => { setIsOpen(false); onExport() }}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-purple-600 transition-colors text-left"
                            >
                                <Download size={16} />
                                Exportar KML
                            </button>
                        )}

                        {(onExport) && <div className="border-t border-gray-100 my-1"></div>}

                        {onDelete && (
                            <button
                                onClick={() => { setIsOpen(false); onDelete() }}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors text-left font-medium"
                            >
                                <Trash2 size={16} />
                                Excluir
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
