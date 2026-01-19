/**
 * Loading Skeleton Components
 * Provides visual feedback while content is loading
 * More intuitive than spinners - shows the structure of what's loading
 */

export function CardSkeleton() {
    return (
        <div className="rounded-lg bg-white p-4 sm:p-6 shadow animate-pulse">
            <div className="flex items-center">
                <div className="flex-shrink-0">
                    <div className="h-8 w-8 bg-gray-200 rounded"></div>
                </div>
                <div className="ml-4 flex-1">
                    <div className="h-3 bg-gray-200 rounded w-20 mb-2"></div>
                    <div className="h-6 bg-gray-200 rounded w-12"></div>
                </div>
            </div>
        </div>
    )
}

export function ListItemSkeleton() {
    return (
        <div className="px-4 sm:px-6 py-3 sm:py-4 animate-pulse">
            <div className="flex items-start sm:items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-48"></div>
                </div>
                <div className="flex gap-2">
                    <div className="h-6 w-16 bg-gray-200 rounded-full"></div>
                    <div className="h-4 w-12 bg-gray-200 rounded"></div>
                </div>
            </div>
        </div>
    )
}

export function GridCardSkeleton() {
    return (
        <div className="rounded-lg bg-white p-4 sm:p-6 shadow animate-pulse">
            <div className="flex items-start justify-between gap-2 mb-4">
                <div className="flex-1">
                    <div className="h-5 bg-gray-200 rounded w-32 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-24"></div>
                </div>
                <div className="h-5 w-16 bg-gray-200 rounded-full"></div>
            </div>
            <div className="flex items-center justify-between">
                <div className="h-3 bg-gray-200 rounded w-16"></div>
                <div className="h-8 w-24 bg-gray-200 rounded"></div>
            </div>
        </div>
    )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="rounded-lg bg-white shadow overflow-hidden">
            <div className="border-b border-gray-200 px-4 sm:px-6 py-3 sm:py-4">
                <div className="h-5 bg-gray-200 rounded w-32 animate-pulse"></div>
            </div>
            <div className="divide-y divide-gray-200">
                {Array.from({ length: rows }).map((_, i) => (
                    <ListItemSkeleton key={i} />
                ))}
            </div>
        </div>
    )
}

export function DashboardSkeleton() {
    return (
        <div className="space-y-6">
            <div className="mb-4 sm:mb-6">
                <div className="h-7 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-64 animate-pulse"></div>
            </div>

            {/* Stats Grid Skeleton */}
            <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
            </div>

            {/* Table Skeleton */}
            <TableSkeleton />
        </div>
    )
}

export function ChatSkeleton() {
    return (
        <div className="space-y-3 sm:space-y-4 p-4 sm:p-6">
            {/* AI Message */}
            <div className="flex justify-start">
                <div className="max-w-[85%] sm:max-w-2xl rounded-lg bg-gray-200 h-16 w-64 animate-pulse"></div>
            </div>
            {/* User Message */}
            <div className="flex justify-end">
                <div className="max-w-[85%] sm:max-w-2xl rounded-lg bg-gray-200 h-12 w-48 animate-pulse"></div>
            </div>
            {/* AI Message */}
            <div className="flex justify-start">
                <div className="max-w-[85%] sm:max-w-2xl rounded-lg bg-gray-200 h-20 w-72 animate-pulse"></div>
            </div>
        </div>
    )
}
