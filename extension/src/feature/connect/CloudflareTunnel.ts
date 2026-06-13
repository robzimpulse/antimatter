import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import { OutboundMessage } from '../../core/network/types';

export class CloudflareTunnel {
  private quickTunnelProcess: ChildProcess | null = null;
  private url: string | null = null;
  private isIntentionalClose: boolean = false;

  constructor(
    private readonly broadcast: (msg: OutboundMessage) => void,
    private readonly log: (msg: string) => void
  ) {}

  async start(port: number): Promise<string | null> {
    const config = vscode.workspace.getConfiguration('antimatter');
    const cloudflareHostname = config.get<string>('cloudflareHostname', '').trim();

    this.isIntentionalClose = false;

    // Mode A: Persistent Zero Trust Configuration
    if (cloudflareHostname) {
      this.log(`Using designated Cloudflare Zero Trust hostname: ${cloudflareHostname}`);
      this.url = `wss://${cloudflareHostname}`;
      setTimeout(() => this.broadcast({ type: 'CLOUDFLARE_URL', url: this.url as string }), 500);
      return this.url;
    }

    // Mode B: Quick Tunnel Fallback
    return new Promise((resolve) => {
      this.log('Starting Cloudflared Quick Tunnel...');
      this.quickTunnelProcess = spawn('cloudflared', ['tunnel', '--url', `http://localhost:${port}`]);

      this.quickTunnelProcess.stderr?.on('data', (data) => {
        const output = data.toString();
        // STAB-002: Two patterns guard against Cloudflare changing their output format.
        // Primary: full https:// URL (current format)
        const primaryMatch = output.match(/https:\/\/[a-zA-Z0-9-]+\.trycloudflare\.com/);
        // Fallback: bare domain name without protocol prefix
        const fallbackMatch = output.match(/([a-zA-Z0-9-]+\.trycloudflare\.com)/);
        const httpUrl = primaryMatch?.[0] ?? (fallbackMatch ? `https://${fallbackMatch[1]}` : null);

        if (httpUrl && !this.url) {
          this.url = httpUrl.replace('https://', 'wss://');
          this.log(`Quick tunnel established: ${this.url}`);
          this.broadcast({ type: 'CLOUDFLARE_URL', url: this.url as string });
        }
      });

      this.quickTunnelProcess.on('close', (code) => {
        if (!this.isIntentionalClose) {
          this.log(`Quick tunnel closed unexpectedly with code ${code}.`);
          this.url = null;
          vscode.window.showWarningMessage('Antimatter tunnel disconnected. Check output logs.');
        }
      });
      
      this.quickTunnelProcess.on('error', (err) => {
        this.log(`Quick tunnel spawn error: ${err.message}`);
      });

      // Resolve immediately so we don't block extension startup
      resolve(null);
    });
  }

  stop() {
    this.isIntentionalClose = true;
    if (this.quickTunnelProcess) {
      this.quickTunnelProcess.kill();
      this.quickTunnelProcess = null;
    }
    this.url = null;
  }

  getUrl(): string | null {
    return this.url;
  }
}
