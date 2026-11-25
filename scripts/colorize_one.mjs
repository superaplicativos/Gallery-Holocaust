const mod = await import('/home/z/.bun/install/global/node_modules/z-ai-web-dev-sdk/dist/index.js');
const ZAI = mod.default ?? mod;
import fs from 'fs';

// usage: node colorize_one.mjs <src> <dst> [size]
const [src, dst, size = '1344x768'] = process.argv.slice(2);
const PROMPT = "Colorize this historical black-and-white documentary photograph with period-accurate, realistic colors: muted earth tones, weathered concrete and brick, overcast sky, natural skin tones preserved exactly as in the original. Keep the original composition, every person, object, building and detail unchanged. Documentary colorization only: do not add, remove or invent any element.";

const b64 = fs.readFileSync(src).toString('base64');
const dataUrl = `data:image/jpeg;base64,${b64}`;

async function main() {
  const zai = await ZAI.create();
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const response = await zai.images.generations.edit({
        prompt: PROMPT,
        images: [{ url: dataUrl }],
        size,
      });
      const b = response?.data?.[0]?.base64;
      if (!b) throw new Error('resposta sem base64');
      fs.writeFileSync(dst, Buffer.from(b, 'base64'));
      console.log(`OK ${dst} (${fs.statSync(dst).size} bytes)`);
      process.exit(0);
    } catch (e) {
      console.error(`attempt ${attempt}: ${String(e.message).slice(0, 160)}`);
      if (attempt === 3) process.exit(1);
      await new Promise(r => setTimeout(r, 2000 * attempt));
    }
  }
}
main();
