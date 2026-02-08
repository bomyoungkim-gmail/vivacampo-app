import dynamicImport from 'next/dynamic'

const MapEmbedClient = dynamicImport(() => import('./MapEmbedClient'), { ssr: false })

export const dynamic = 'force-dynamic'

export default function MapEmbedPage() {
    return <MapEmbedClient />
}
