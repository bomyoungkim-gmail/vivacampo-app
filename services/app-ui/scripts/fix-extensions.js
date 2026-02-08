const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const INPUT_DIR = path.join(__dirname, '../public/landing');
const files = fs.readdirSync(INPUT_DIR).filter(file => file.endsWith('.png'));

async function fixExtensions() {
    console.log(`🔍 Verificando ${files.length} arquivos...`);

    for (const file of files) {
        const filePath = path.join(INPUT_DIR, file);
        try {
            const metadata = await sharp(filePath).metadata();

            if (metadata.format === 'jpeg') {
                const newPath = filePath.replace('.png', '.jpg');
                fs.renameSync(filePath, newPath);
                console.log(`✅ Renomeado: ${file} -> ${path.basename(newPath)} (Era JPEG mascarado)`);
            } else {
                console.log(`ℹ️  Mantido: ${file} é realmente ${metadata.format}`);
            }
        } catch (err) {
            console.error(`❌ Erro em ${file}:`, err.message);
        }
    }
}

fixExtensions();
