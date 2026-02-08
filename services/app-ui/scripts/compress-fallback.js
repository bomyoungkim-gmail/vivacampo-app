const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const INPUT_DIR = path.join(__dirname, '../public/landing');
const OUTPUT_DIR = path.join(__dirname, '../public/landing/compressed');

if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function compressValues() {
    const files = fs.readdirSync(INPUT_DIR).filter(file => file.endsWith('.png') || file.endsWith('.jpg'));

    console.log(`🚀 Iniciando compressão de fallback (WebP/AVIF) para ${files.length} arquivos...`);

    for (const file of files) {
        const inputPath = path.join(INPUT_DIR, file);
        const filename = path.parse(file).name;

        console.log(`📸 Processando ${file}...`);

        // WebP (Alta compatibilidade + boa compressão)
        await sharp(inputPath)
            .webp({ quality: 80, effort: 6 })
            .toFile(path.join(OUTPUT_DIR, `${filename}.webp`));

        console.log(`   ✅ ${filename}.webp gerado`);

        // AVIF (Melhor compressão, suporte moderno)
        await sharp(inputPath)
            .avif({ quality: 75, effort: 5 })
            .toFile(path.join(OUTPUT_DIR, `${filename}.avif`));

        console.log(`   ✅ ${filename}.avif gerado`);
    }

    console.log('\n==================================================');
    console.log('✅ COMPRESSÃO FALLBACK CONCLUÍDA!');
    console.log('==================================================\n');
}

compressValues().catch(err => {
    console.error('❌ Erro na compressão:', err);
    process.exit(1);
});
