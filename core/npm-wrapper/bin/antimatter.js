#!/usr/bin/env node
const { spawnSync } = require('child_process');

console.log('🚀 Booting Antimatter Gateway via uvx...');
const args = process.argv.slice(2);
const result = spawnSync('uvx', ['antimatter-gateway', ...args], { stdio: 'inherit', shell: true });

if (result.error || result.status !== 0) {
    console.error('\n❌ Failed to start the Antimatter Gateway.');
    console.error('Please ensure you have "uv" installed. You can install it using:');
    console.error('curl -LsSf https://astral.sh/uv/install.sh | sh');
    console.error('Or simply install directly via pip: pip install antimatter-gateway');
    process.exit(1);
}
