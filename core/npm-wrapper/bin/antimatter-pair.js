#!/usr/bin/env node
const { spawnSync } = require('child_process');

console.log('🚀 Booting Antimatter Pairing tool via uvx...');
const args = process.argv.slice(2);
const result = spawnSync('uvx', ['antimatter-gateway', 'pair', ...args], { stdio: 'inherit', shell: true });

if (result.error || result.status !== 0) {
    console.error('\n❌ Failed to start the Antimatter Pair tool.');
    console.error('Please ensure you have "uv" installed. You can install it using:');
    console.error('curl -LsSf https://astral.sh/uv/install.sh | sh');
    console.error('Or simply install directly via pip: pip install antimatter-gateway');
    process.exit(1);
}
