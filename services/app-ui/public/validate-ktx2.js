/**
 * Script de Validação KTX2 - Chrome DevTools Console
 *
 * Como usar:
 * 1. Abrir http://localhost:3000
 * 2. Abrir DevTools > Console
 * 3. Copiar e colar este script
 * 4. Analisar resultado
 *
 * @author VivaCampo Team
 * @date 2025-02-07
 */

(function validateKTX2Compression() {
  console.log('%c🔍 Validando Compressão KTX2...', 'color: #3b82f6; font-size: 16px; font-weight: bold');
  console.log('');

  // ========================================
  // 1. Verificar texturas carregadas
  // ========================================
  console.group('📦 Texturas Carregadas');

  const textures = performance.getEntriesByType('resource')
    .filter(entry =>
      entry.name.includes('/textures/') &&
      (entry.name.endsWith('.ktx2') || entry.name.endsWith('.jpg') || entry.name.endsWith('.png'))
    );

  if (textures.length === 0) {
    console.warn('⚠️  Nenhuma textura encontrada. Aguarde o carregamento da página.');
    console.groupEnd();
    return;
  }

  let ktx2Count = 0;
  let fallbackCount = 0;
  let totalSize = 0;

  textures.forEach(texture => {
    const name = texture.name.split('/').pop();
    const size = (texture.transferSize / 1024).toFixed(2);
    const isKTX2 = name.endsWith('.ktx2');

    if (isKTX2) {
      ktx2Count++;
      console.log(`✅ ${name} - ${size} KB (KTX2)`, { duration: texture.duration.toFixed(2) + 'ms' });
    } else {
      fallbackCount++;
      console.log(`⚠️  ${name} - ${size} KB (FALLBACK)`, { duration: texture.duration.toFixed(2) + 'ms' });
    }

    totalSize += parseFloat(size);
  });

  console.log('');
  console.log(`📊 Total: ${textures.length} texturas, ${totalSize.toFixed(2)} KB`);
  console.log(`   KTX2: ${ktx2Count} | Fallback (JPG/PNG): ${fallbackCount}`);
  console.groupEnd();

  // ========================================
  // 2. Verificar suporte WebGL
  // ========================================
  console.log('');
  console.group('🎮 Suporte WebGL');

  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');

  if (!gl) {
    console.error('❌ WebGL não suportado neste navegador!');
    console.groupEnd();
    return;
  }

  const compressionFormats = [
    { name: 'ETC1', ext: 'WEBGL_compressed_texture_etc1' },
    { name: 'ETC2', ext: 'WEBGL_compressed_texture_etc' },
    { name: 'ASTC', ext: 'WEBGL_compressed_texture_astc' },
    { name: 'S3TC (DXT)', ext: 'WEBGL_compressed_texture_s3tc' },
    { name: 'PVRTC', ext: 'WEBGL_compressed_texture_pvrtc' },
    { name: 'BC7', ext: 'EXT_texture_compression_bptc' }
  ];

  compressionFormats.forEach(format => {
    const supported = gl.getExtension(format.ext) !== null;
    const icon = supported ? '✅' : '❌';
    console.log(`${icon} ${format.name}`);
  });

  console.groupEnd();

  // ========================================
  // 3. Estimar uso de VRAM
  // ========================================
  console.log('');
  console.group('💾 Estimativa de VRAM');

  // Assumindo texturas 2048x1024 (earth_day) + 1024x512 (earth_clouds)
  const earthDayPixels = 2048 * 1024;
  const earthCloudsPixels = 1024 * 512;
  const bytesPerPixel = 4; // RGBA

  if (ktx2Count > 0) {
    // KTX2 usa compressão ~8:1 para ETC1s/UASTC
    const compressedVRAM = ((earthDayPixels + earthCloudsPixels) * bytesPerPixel) / 8;
    console.log(`📊 VRAM Estimada (KTX2): ~${(compressedVRAM / 1024 / 1024).toFixed(2)} MB`);
    console.log(`   Compressão: ~8:1`);
  } else {
    // Sem compressão
    const uncompressedVRAM = (earthDayPixels + earthCloudsPixels) * bytesPerPixel;
    console.log(`📊 VRAM Estimada (JPG/PNG): ~${(uncompressedVRAM / 1024 / 1024).toFixed(2)} MB`);
    console.log(`   ⚠️  Sem compressão GPU`);
  }

  console.groupEnd();

  // ========================================
  // 4. Recomendações
  // ========================================
  console.log('');
  console.group('💡 Recomendações');

  if (ktx2Count === 0) {
    console.warn('⚠️  KTX2 não está sendo usado!');
    console.log('');
    console.log('Passos para resolver:');
    console.log('1. Gerar assets KTX2: npm run generate:ktx2');
    console.log('2. Verificar se arquivos existem: ls public/textures/compressed/*.ktx2');
    console.log('3. Recarregar página');
    console.log('');
    console.log('Documentação: services/app-ui/docs/KTX2_COMPRESSION.md');
  } else if (fallbackCount > 0) {
    console.log('⚠️  Algumas texturas usam fallback (JPG/PNG)');
    console.log('Isso pode ser normal se:');
    console.log('- Versão mobile não foi gerada (ImageMagick não instalado)');
    console.log('- Arquivo .ktx2 específico não existe');
  } else {
    console.log('✅ Todas as texturas usam KTX2!');
    console.log('🎉 Compressão GPU otimizada ativa.');
    console.log('');
    console.log('Ganhos estimados:');
    console.log('- 70% redução de tamanho de arquivo');
    console.log('- 87% redução de VRAM');
    console.log('- +15 FPS em dispositivos mobile');
  }

  console.groupEnd();

  // ========================================
  // 5. Informações de Hardware
  // ========================================
  console.log('');
  console.group('🖥️  Hardware Info');

  const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
  if (debugInfo) {
    const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
    const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
    console.log(`GPU: ${vendor} - ${renderer}`);
  }

  console.log(`Cores: ${navigator.hardwareConcurrency || 'N/A'}`);
  console.log(`Device Memory: ${navigator.deviceMemory || 'N/A'} GB`);
  console.log(`User Agent: ${navigator.userAgent.match(/(Chrome|Firefox|Safari)\/[\d.]+/)?.[0] || 'Unknown'}`);

  console.groupEnd();

  console.log('');
  console.log('%c✅ Validação Completa!', 'color: #10b981; font-size: 14px; font-weight: bold');
  console.log('');
})();
