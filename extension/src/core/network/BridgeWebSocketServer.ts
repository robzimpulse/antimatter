import { WebSocketServer, WebSocket } from 'ws';
import * as vscode from 'vscode';
import { ConnectionManager } from '../../feature/connect/ConnectionManager';
import { AuthHandler } from '../../feature/connect/AuthHandler';
import { MessageRouter } from './MessageRouter';
import { CloudflareTunnel } from '../../feature/connect/CloudflareTunnel';

export class BridgeWebSocketServer {
  private wss: WebSocketServer | null = null;
  private ipFailureCounts = new Map<string, { count: number; resetAt: number }>();

  constructor(
    private connectionManager: ConnectionManager,
    private authHandler: AuthHandler,
    private router: MessageRouter,
    private tunnel: CloudflareTunnel,
    private log: (msg: string) => void
  ) {}

  start(port: number) {
    if (this.wss) {
      this.log('Bridge already running.');
      return;
    }

    try {
      this.wss = new WebSocketServer({ 
        port, 
        host: '127.0.0.1',
        verifyClient: (info, cb) => {
          const origin = info.req.headers.origin;
          if (origin && !origin.startsWith('vscode-webview://') && !/^https:\/\/[a-zA-Z0-9-]+\.cloudflareaccess\.com$/.test(origin)) {
            return cb(false, 403, 'Forbidden Origin');
          }
          cb(true);
        },
        perMessageDeflate: {
          zlibDeflateOptions: { chunkSize: 1024, memLevel: 7, level: 3 },
          zlibInflateOptions: { chunkSize: 10 * 1024 },
          threshold: 1024
        },
        maxPayload: 10 * 1024 * 1024
      });
      
      this.log(`WebSocket server started on port ${port}`);

      this.wss.on('connection', (ws, req) => {
        const remoteAddr = req.socket.remoteAddress ?? 'unknown';
        const now = Date.now();

        // Rate Limiting
        const failData = this.ipFailureCounts.get(remoteAddr);
        if (failData && failData.count >= 5 && now < failData.resetAt) {
          this.log(`Client blocked due to rate limiting: ${remoteAddr}`);
          ws.close(4000, 'Rate Limited');
          return;
        }

        // Token Extraction
        let token = '';
        try {
          const authHeader = req.headers['authorization'];
          if (authHeader && authHeader.startsWith('Bearer ')) {
            token = authHeader.substring(7);
          } else if (req.headers['sec-websocket-protocol']) {
            const protocols = req.headers['sec-websocket-protocol'].split(',').map(p => p.trim());
            if (protocols.length > 0) token = protocols[0];
          } else {
            const urlObj = new URL(req.url || '', 'http://localhost');
            token = urlObj.searchParams.get('token') || '';
          }
        } catch (e) { }

        // Token Verification
        if (!this.authHandler.verifyToken(token)) {
          this.log(`Unauthorized connection attempt from ${remoteAddr} (Invalid Token)`);
          const count = (failData?.count || 0) + 1;
          this.ipFailureCounts.set(remoteAddr, { count, resetAt: now + 60000 }); // 1 min ban
          ws.close(4001, 'Unauthorized');
          return;
        }

        this.log(`Client connected (pending handshake): ${remoteAddr}`);
        this.connectionManager.addClient(ws);

        // Set up the router listener
        ws.on('message', (raw) => {
          this.router.route(raw.toString(), ws);
        });

        ws.on('close', () => {
          this.log(`Client disconnected: ${remoteAddr}`);
          this.connectionManager.removeClient(ws);
        });

        ws.on('error', (err) => {
          this.log(`Client error (${remoteAddr}): ${err.message}`);
          this.connectionManager.removeClient(ws);
        });
        
        // PING/PONG keepalive could be added here
      });

      this.wss.on('error', (err) => {
        this.log(`WebSocket server error: ${err.message}`);
        vscode.window.showErrorMessage(`Antimatter Bridge error: ${err.message}`);
      });

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      this.log(`Failed to start WebSocket Server: ${message}`);
      throw err;
    }
  }

  stop() {
    if (this.wss) {
      this.wss.close();
      this.wss = null;
    }
  }
}
