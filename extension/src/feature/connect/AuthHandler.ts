import * as crypto from 'crypto';
import * as vscode from 'vscode';
import { ConnectionManager } from './ConnectionManager';
import { WebSocket } from 'ws';

export class AuthHandler {
  private globalPairingToken!: string;
  private bridgeKeyPair!: crypto.KeyPairKeyObjectResult;
  private bridgePublicKeyRawBase64!: string;

  constructor(
    private context: vscode.ExtensionContext,
    private connectionManager: ConnectionManager,
    private log: (msg: string) => void
  ) {}

  async init() {
    // 1. Restore or generate 32-byte pairing token from SecretStorage
    let token = await this.context.secrets.get('pairingToken');
    if (!token) {
      // Fallback: try to migrate from globalState
      token = this.context.globalState.get<string>('pairingToken');
      if (token) {
        await this.context.secrets.store('pairingToken', token);
        this.context.globalState.update('pairingToken', undefined);
      } else {
        token = crypto.randomBytes(32).toString('base64url');
        await this.context.secrets.store('pairingToken', token);
      }
    }
    this.globalPairingToken = token;

    // 2. Restore or generate Ed25519 keypair for local cryptographic handshake
    let privateKeyPem = await this.context.secrets.get('bridgePrivateKey');
    let publicKeyPem = await this.context.secrets.get('bridgePublicKey');

    // Migration from globalState if needed
    if (!privateKeyPem || !publicKeyPem) {
      privateKeyPem = this.context.globalState.get<string>('bridgePrivateKey');
      publicKeyPem = this.context.globalState.get<string>('bridgePublicKey');
      if (privateKeyPem && publicKeyPem) {
        await this.context.secrets.store('bridgePrivateKey', privateKeyPem);
        await this.context.secrets.store('bridgePublicKey', publicKeyPem);
        this.context.globalState.update('bridgePrivateKey', undefined);
        this.context.globalState.update('bridgePublicKey', undefined);
      }
    }

    if (privateKeyPem && publicKeyPem) {
      this.bridgeKeyPair = {
        privateKey: crypto.createPrivateKey(privateKeyPem),
        publicKey: crypto.createPublicKey(publicKeyPem)
      };
      this.log(`Restored persistent Ed25519 keypair from SecretStorage`);
    } else {
      this.bridgeKeyPair = crypto.generateKeyPairSync('ed25519');
      await this.context.secrets.store('bridgePrivateKey', this.bridgeKeyPair.privateKey.export({ type: 'pkcs8', format: 'pem' }).toString());
      await this.context.secrets.store('bridgePublicKey', this.bridgeKeyPair.publicKey.export({ type: 'spki', format: 'pem' }).toString());
      this.log(`Generated new persistent Ed25519 keypair in SecretStorage`);
    }
    
    const pubKeyBuffer = this.bridgeKeyPair.publicKey.export({ type: 'spki', format: 'der' });
    this.bridgePublicKeyRawBase64 = Buffer.isBuffer(pubKeyBuffer) 
      ? pubKeyBuffer.subarray(12).toString('base64')
      : Buffer.from(pubKeyBuffer as any).subarray(12).toString('base64');
  }

  getPairingToken(): string {
    return this.globalPairingToken;
  }

  getPublicKeyRawBase64(): string {
    return this.bridgePublicKeyRawBase64;
  }

  verifyToken(providedToken: string): boolean {
    try {
      const providedBuffer = Buffer.from(providedToken, 'utf8');
      const expectedBuffer = Buffer.from(this.globalPairingToken, 'utf8');
      
      if (providedBuffer.length !== expectedBuffer.length || !crypto.timingSafeEqual(providedBuffer, expectedBuffer)) {
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }

  handleAuthChallenge(ws: WebSocket, challenge: string) {
    try {
      const nonceBuffer = Buffer.from(challenge, 'base64');
      const signature = crypto.sign(null, nonceBuffer, this.bridgeKeyPair.privateKey);
      
      this.connectionManager.authenticateClient(ws);
      this.log(`Client authenticated successfully via Ed25519 challenge.`);
      
      ws.send(JSON.stringify({ type: 'AUTH_RESPONSE', signature: signature.toString('base64') }));
    } catch (e) {
      this.log(`Failed to sign AUTH_CHALLENGE`);
      ws.send(JSON.stringify({ type: 'ERROR', message: 'Auth Failed' }));
    }
  }
}
