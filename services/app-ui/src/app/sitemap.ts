import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://vivacampo.ag'

    return [
        {
            url: `${baseUrl}/`,
            lastModified: new Date('2026-02-07'),
            changeFrequency: 'weekly',
            priority: 1,
        },
        {
            url: `${baseUrl}/pricing`,
            lastModified: new Date('2026-02-07'),
            changeFrequency: 'monthly',
            priority: 0.8,
        },
        {
            url: `${baseUrl}/docs/api`,
            lastModified: new Date('2026-02-07'),
            changeFrequency: 'weekly',
            priority: 0.7,
        },
    ]
}
