import * as vscode from 'vscode';
import * as QRCode from 'qrcode';

export class QrWebviewProvider {
  constructor(private log: (msg: string) => void) {}

  async showPairingQR(url: string | null, token: string, pubkey: string, cfId: string, cfSecret: string) {
    if (!url) {
      vscode.window.showErrorMessage('Antimatter Bridge is still starting up or failed to get a tunnel URL. Check logs.');
      return;
    }

    // Generate secure HTTPS App Link for Android intent filtering
    let pairingUrl = `https://antimatter.saifmukhtar.dev/connect?url=${encodeURIComponent(url)}&token=${encodeURIComponent(token)}&pubkey=${encodeURIComponent(pubkey)}`;
    if (cfId && cfSecret) {
      pairingUrl += `&cfid=${encodeURIComponent(cfId)}&cfsec=${encodeURIComponent(cfSecret)}`;
    }

    try {
      const qrDataUrl = await QRCode.toDataURL(pairingUrl, {
        errorCorrectionLevel: 'M',
        margin: 2,
        width: 400,
        color: { dark: '#000000FF', light: '#FFFFFFFF' }
      });

      const panel = vscode.window.createWebviewPanel(
        'antimatterQR',
        'Antimatter Pairing QR',
        vscode.ViewColumn.One,
        { enableScripts: true }
      );

      panel.webview.html = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <style>
            body { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background-color: var(--vscode-editor-background); color: var(--vscode-editor-foreground); font-family: var(--vscode-font-family); margin: 0; }
            .container { text-align: center; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
            h2 { color: #333; margin-top: 0; }
            img { max-width: 100%; border: 1px solid #eee; border-radius: 4px; }
            p { margin-top: 1rem; color: #666; max-width: 400px; font-size: 14px; }
            .token-box { margin-top: 1rem; background: #f4f4f4; padding: 0.5rem; border-radius: 6px; font-family: monospace; color: #333; word-break: break-all; }
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Pair Device</h2>
            <img src="${qrDataUrl}" alt="Pairing QR Code"/>
            <p>Scan this QR code with the Antimatter Android app to securely connect your device.</p>
            <p><strong>Manual Connection Token:</strong></p>
            <div class="token-box">${token}</div>
          </div>
        </body>
        </html>
      `;
    } catch (err) {
      vscode.window.showErrorMessage('Failed to generate QR code.');
      this.log(`QR Generation Error: ${err}`);
    }
  }
}
