import WebSocket from 'ws';
import { randomUUID } from 'crypto';
import * as vscode from 'vscode';
import * as os from 'os';
import * as fs from 'fs';
import * as path from 'path';
import { ConnectionManager } from '../../feature/connect/ConnectionManager';
import { MessageRouter } from './MessageRouter';

export class GatewayClient {
    private client: WebSocket | null = null;
    private gatewayUrl: string;
    // Stable ID for this adapter instance — generated once per VS Code session
    private readonly adapterId: string = randomUUID();

    constructor(
        private connectionManager: ConnectionManager,
        private router: MessageRouter,
        private workspaceRoot: string,
        private log: (msg: string) => void
    ) {
        const port = vscode.workspace.getConfiguration('antimatter').get<number>('port') || 8765;
        this.gatewayUrl = `ws://127.0.0.1:${port}`;
    }

    public start() {
        this.connect();
    }

    private connect() {
        this.log(`Connecting to Gateway at ${this.gatewayUrl}...`);
        this.client = new WebSocket(this.gatewayUrl);

        this.client.on('open', () => {
            this.log('Connected to Gateway IPC.');
            
            let ipcToken = '';
            try {
                // VS Code might be running in a Snap or Flatpak sandbox where os.homedir()
                // returns a sandboxed path (e.g. ~/snap/code/...). We try multiple fallbacks.
                const username = (os.userInfo() || {}).username;
                const isMac = process.platform === 'darwin';
                const isWin = process.platform === 'win32';
                
                let dynamicHome = '';
                if (isWin) {
                    dynamicHome = process.env.USERPROFILE || '';
                } else if (isMac) {
                    dynamicHome = username ? `/Users/${username}` : '';
                } else {
                    dynamicHome = username === 'root' ? '/root' : (username ? `/home/${username}` : '');
                }

                const possibleHomes = [
                    os.homedir(),
                    process.env.HOME,
                    (os.userInfo() || {}).homedir,
                    dynamicHome
                ].filter(Boolean) as string[];

                // Unique paths
                const uniqueHomes = [...new Set(possibleHomes)];

                for (const home of uniqueHomes) {
                    const tokenPath = path.join(home, '.antimatter_daemon', '.ipc_token');
                    if (fs.existsSync(tokenPath)) {
                        ipcToken = fs.readFileSync(tokenPath, 'utf8').trim();
                        this.log(`Successfully read IPC token from: ${tokenPath}`);
                        break;
                    }
                }

                if (!ipcToken) {
                    this.log(`CRITICAL: Could not find .ipc_token in any checked home directories: ${uniqueHomes.join(', ')}`);
                }
            } catch (e) {
                this.log(`Failed to read IPC token: ${e}`);
            }

            // Register as the ag adapter, sending a stable UUID so the Gateway
            // can correctly key this adapter for targeted IPC routing.
            this.client!.send(JSON.stringify({
                type: 'REGISTER_ADAPTER',
                id: this.adapterId,
                name: 'ag',
                ipc_token: ipcToken,
                workspaceRoot: this.workspaceRoot
            }));
            // Update the ConnectionManager with the fresh socket after every
            // (re)connect so broadcasts never use a stale reference.
            this.connectionManager.setGatewayClient(this.client as any);
        });

        this.client.on('message', async (data: WebSocket.RawData) => {
            try {
                const messageStr = data.toString();
                const payload = JSON.parse(messageStr);
                
                // Route through the existing router
                await this.router.route(payload, this.client!);
            } catch (error) {
                this.log(`Error parsing IPC message: ${error}`);
            }
        });

        this.client.on('close', () => {
            this.log('Disconnected from Gateway. Reconnecting in 3s...');
            setTimeout(() => this.connect(), 3000);
        });

        this.client.on('error', (err) => {
            this.log(`IPC Connection Error: ${err.message}`);
        });
    }

    public stop() {
        if (this.client) {
            this.client.close();
            this.client = null;
        }
    }
}
