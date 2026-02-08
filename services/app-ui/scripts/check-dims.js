const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const INPUT_DIR = path.join(__dirname, '../public/textures');
const files = fs.readdirSync(INPUT_DIR).filter(file => file.endsWith('.png') || file.endsWith('.jpg'));

async function checkDims() {
    for (const file of files) {
        const inputPath = path.join(INPUT_DIR, file);
        const metadata = await sharp(inputPath).metadata();
        console.log(`${file}: ${metadata.width}x${metadata.height} (${metadata.format})`);
    }
}
checkDims();
