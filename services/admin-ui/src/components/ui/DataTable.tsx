'use client'

import { useState, useMemo, ReactNode } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Card, CardContent } from './Card'
import { Skeleton } from './Skeleton'

export interface Column<T> {
    key: string
    header: string
    accessor?: (row: T) => ReactNode
    sortable?: boolean
    className?: string
    mobileLabel?: string // Label for mobile card view
}

export interface DataTableProps<T> {
    data: T[]
    columns: Column<T>[]
    loading?: boolean
    emptyMessage?: string
    rowKey: (row: T) => string | number
    onRowClick?: (row: T) => void
    mobileCardRender?: (row: T) => ReactNode // Custom mobile card renderer
}

type SortDirection = 'asc' | 'desc' | null

export function DataTable<T extends Record<string, any>>({
    data,
    columns,
    loading = false,
    emptyMessage = 'Nenhum dado encontrado',
    rowKey,
    onRowClick,
    mobileCardRender,
}: DataTableProps<T>) {
    const [sortKey, setSortKey] = useState<string | null>(null)
    const [sortDirection, setSortDirection] = useState<SortDirection>(null)

    // Sorting logic
    const sortedData = useMemo(() => {
        if (!sortKey || !sortDirection) return data

        return [...data].sort((a, b) => {
            const column = columns.find((col) => col.key === sortKey)
            if (!column) return 0

            const aValue = column.accessor ? column.accessor(a) : a[sortKey]
            const bValue = column.accessor ? column.accessor(b) : b[sortKey]

            // Handle null/undefined
            if (aValue == null && bValue == null) return 0
            if (aValue == null) return sortDirection === 'asc' ? 1 : -1
            if (bValue == null) return sortDirection === 'asc' ? -1 : 1

            // String comparison
            const aStr = String(aValue).toLowerCase()
            const bStr = String(bValue).toLowerCase()

            if (aStr < bStr) return sortDirection === 'asc' ? -1 : 1
            if (aStr > bStr) return sortDirection === 'asc' ? 1 : -1
            return 0
        })
    }, [data, sortKey, sortDirection, columns])

    const handleSort = (key: string) => {
        const column = columns.find((col) => col.key === key)
        if (!column?.sortable) return

        if (sortKey === key) {
            // Cycle: asc -> desc -> null
            if (sortDirection === 'asc') {
                setSortDirection('desc')
            } else if (sortDirection === 'desc') {
                setSortKey(null)
                setSortDirection(null)
            }
        } else {
            setSortKey(key)
            setSortDirection('asc')
        }
    }

    const getSortIcon = (key: string) => {
        if (sortKey !== key) return <ArrowUpDown className="h-4 w-4 opacity-50" />
        if (sortDirection === 'asc') return <ArrowUp className="h-4 w-4" />
        return <ArrowDown className="h-4 w-4" />
    }

    // Loading state
    if (loading) {
        return (
            <div className="space-y-2">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
            </div>
        )
    }

    // Empty state
    if (sortedData.length === 0) {
        return (
            <div className="rounded-lg border border-border bg-card p-12 text-center">
                <p className="text-muted-foreground">{emptyMessage}</p>
            </div>
        )
    }

    // Mobile view (cards)
    const MobileView = () => (
        <div className="block lg:hidden space-y-4">
            {sortedData.map((row) => {
                if (mobileCardRender) {
                    return (
                        <div
                            key={rowKey(row)}
                            onClick={() => onRowClick?.(row)}
                            className={onRowClick ? 'cursor-pointer' : ''}
                        >
                            {mobileCardRender(row)}
                        </div>
                    )
                }

                return (
                    <Card
                        key={rowKey(row)}
                        onClick={() => onRowClick?.(row)}
                        className={onRowClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}
                    >
                        <CardContent className="p-4 space-y-2">
                            {columns.map((column) => {
                                const value = column.accessor ? column.accessor(row) : row[column.key]
                                return (
                                    <div key={column.key} className="flex justify-between items-start">
                                        <span className="text-sm font-medium text-muted-foreground">
                                            {column.mobileLabel || column.header}:
                                        </span>
                                        <span className="text-sm text-foreground text-right ml-2">
                                            {value}
                                        </span>
                                    </div>
                                )
                            })}
                        </CardContent>
                    </Card>
                )
            })}
        </div>
    )

    // Desktop view (table)
    const DesktopView = () => (
        <div className="hidden lg:block rounded-lg border border-border bg-card shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50">
                        <tr>
                            {columns.map((column) => (
                                <th
                                    key={column.key}
                                    onClick={() => handleSort(column.key)}
                                    className={`px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider ${
                                        column.sortable ? 'cursor-pointer select-none hover:bg-muted transition-colors' : ''
                                    } ${column.className || ''}`}
                                >
                                    <div className="flex items-center gap-2">
                                        {column.header}
                                        {column.sortable && getSortIcon(column.key)}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {sortedData.map((row) => (
                            <tr
                                key={rowKey(row)}
                                onClick={() => onRowClick?.(row)}
                                className={
                                    onRowClick
                                        ? 'table-row-interactive'
                                        : 'hover:bg-muted/50 transition-colors'
                                }
                            >
                                {columns.map((column) => {
                                    const value = column.accessor ? column.accessor(row) : row[column.key]
                                    return (
                                        <td
                                            key={column.key}
                                            className={`px-6 py-4 text-sm text-foreground ${
                                                column.className || ''
                                            }`}
                                        >
                                            {value}
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )

    return (
        <>
            <MobileView />
            <DesktopView />
        </>
    )
}
