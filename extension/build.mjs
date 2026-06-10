import * as esbuild from 'esbuild';
import { argv } from 'process';

const watch = argv.includes('--watch');

const buildOptions = {
  entryPoints: ['src/extension.ts'],
  bundle: true,
  outfile: 'dist/extension.js',
  external: ['vscode'],       // vscode is provided by the host — never bundle it
  format: 'cjs',
  platform: 'node',
  target: 'node22',
  sourcemap: false,
  minify: true,              // keep readable for debugging
  logLevel: 'info',
};

if (watch) {
  const ctx = await esbuild.context(buildOptions);
  await ctx.watch();
  console.log('Watching for changes...');
} else {
  await esbuild.build(buildOptions);
  console.log('Build complete → dist/extension.js');
}
