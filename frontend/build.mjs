// Gera static/dist a partir de frontend/. O resultado é versionado: rodar o app não exige Node.
import * as esbuild from 'esbuild';

const comum = { bundle: true, minify: true, target: 'es2022', logLevel: 'info', legalComments: 'none' };

const alvos = [
  { ...comum, entryPoints: ['frontend/src/main.ts'], outfile: 'static/dist/app.js', format: 'esm' },
  { ...comum, entryPoints: ['frontend/src/boot.ts'], outfile: 'static/dist/boot.js', format: 'iife' },
  { ...comum, entryPoints: ['frontend/css/main.css'], outfile: 'static/dist/main.css' },
  { ...comum, entryPoints: ['frontend/css/media.css'], outfile: 'static/dist/media.css' },
];

if (process.argv.includes('--watch')) {
  for (const alvo of alvos) {
    const ctx = await esbuild.context(alvo);
    await ctx.watch();
  }
} else {
  await Promise.all(alvos.map((alvo) => esbuild.build(alvo)));
}
