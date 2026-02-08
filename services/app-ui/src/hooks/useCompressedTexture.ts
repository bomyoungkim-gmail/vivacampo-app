'use client'

import { useEffect, useState } from 'react'
import { Texture, TextureLoader, WebGLRenderer } from 'three'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'

/**
 * Hook para carregar texturas com compressão KTX2/Basis + fallback para JPG/PNG
 *
 * **Benefícios KTX2:**
 * - Compressão GPU-nativa (ETC1s, UASTC)
 * - Reduz uso de VRAM em 75-90%
 * - Carregamento mais rápido (sem decode de JPG/PNG)
 * - Suporte a mipmaps otimizados
 *
 * **Fallback Automático:**
 * - Se .ktx2 falhar ou não existir, carrega JPG/PNG
 * - Compatibilidade com navegadores antigos
 *
 * @example
 * ```tsx
 * const [dayMap, cloudsMap] = useCompressedTexture([
 *   { ktx2: '/textures/compressed/earth_day.ktx2', fallback: '/textures/earth_day_2048.jpg' },
 *   { ktx2: '/textures/compressed/earth_clouds.ktx2', fallback: '/textures/earth_clouds_1024.png' }
 * ])
 * ```
 */

interface TextureSource {
  /** Caminho para arquivo .ktx2 (preferencial) */
  ktx2: string
  /** Caminho para fallback JPG/PNG */
  fallback: string
  /** Versão mobile (opcional, < 1MB) */
  mobile?: string
}

// Singleton KTX2Loader (reutiliza instância)
let ktx2Loader: KTX2Loader | null = null
const DEBUG_TEXTURES = process.env.NODE_ENV !== 'production'

function getKTX2Loader(): KTX2Loader {
  if (!ktx2Loader && typeof window !== 'undefined') {
    ktx2Loader = new KTX2Loader()
    // Transcoder WASM path (fornecido por three-stdlib)
    ktx2Loader.setTranscoderPath('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/basis/')
    try {
      const canvas = document.createElement('canvas')
      const renderer = new WebGLRenderer({ canvas })
      ktx2Loader.detectSupport(renderer)
      renderer.dispose()
      if (DEBUG_TEXTURES) {
        console.log('🧪 KTX2 detectSupport: OK')
      }
    } catch (error) {
      console.warn('⚠️  WebGL not available for KTX2 detectSupport.', error)
    }
  }
  return ktx2Loader!
}

/**
 * Detecta se o dispositivo é mobile (para usar versão LOD reduzida)
 */
function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

/**
 * Carrega uma única textura com KTX2 + fallback
 */
async function loadTexture(source: TextureSource): Promise<Texture> {
  const loader = getKTX2Loader()
  const textureLoader = new TextureLoader()

  // Usar versão mobile se disponível e for dispositivo mobile
  const ktx2Path = isMobileDevice() && source.mobile ? source.mobile : source.ktx2

  try {
    if (DEBUG_TEXTURES) {
      console.log('🧪 KTX2 load start:', ktx2Path)
    }
    // Tentar carregar KTX2 primeiro
    const texture = await new Promise<Texture>((resolve, reject) => {
      loader.load(
        ktx2Path,
        (texture) => resolve(texture),
        undefined,
        (error) => reject(error)
      )
    })

    console.log(`✅ KTX2 loaded: ${ktx2Path}`)
    return texture

  } catch (error) {
    // Fallback para JPG/PNG
    console.warn(`⚠️  KTX2 failed, using fallback: ${source.fallback}`, error)

    return new Promise<Texture>((resolve, reject) => {
      textureLoader.load(
        source.fallback,
        (texture) => {
          console.log(`✅ Fallback loaded: ${source.fallback}`)
          resolve(texture)
        },
        undefined,
        (fallbackError) => {
          console.error(`❌ Fallback failed: ${source.fallback}`, fallbackError)
          reject(fallbackError)
        }
      )
    })
  }
}

/**
 * Hook para carregar múltiplas texturas com KTX2 + fallback
 */
export function useCompressedTexture(sources: TextureSource[]): (Texture | null)[] {
  const [textures, setTextures] = useState<(Texture | null)[]>(
    sources.map(() => null)
  )

  useEffect(() => {
    let isMounted = true

    async function loadAll() {
      if (DEBUG_TEXTURES) {
        console.log('🧪 useCompressedTexture mount', sources)
      }
      try {
        const loadedTextures = await Promise.all(
          sources.map(source => loadTexture(source))
        )

        if (isMounted) {
          setTextures(loadedTextures)
        }
      } catch (error) {
        console.error('❌ useCompressedTexture loadAll failed', error)
      }
    }

    loadAll()

    return () => {
      isMounted = false
      if (DEBUG_TEXTURES) {
        console.log('🧪 useCompressedTexture unmount')
      }
      // Cleanup: dispose texturas quando componente desmontar
      textures.forEach(texture => texture?.dispose())
    }
  }, []) // Carregar apenas uma vez

  return textures
}
