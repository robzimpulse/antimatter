import * as vscode from 'vscode';
import { ConnectionManager } from './feature/connect/ConnectionManager';
import { ChatStateManager } from './core/state/ChatStateManager';
import { MessageRouter } from './core/network/MessageRouter';
import { CloudflareTunnel } from './feature/connect/CloudflareTunnel';
import { BridgeWebSocketServer } from './core/network/BridgeWebSocketServer';
import { BrainWatcher } from './feature/chat/BrainWatcher';
import { AuthHandler } from './feature/connect/AuthHandler';
import { ChatCommandHandler } from './feature/chat/ChatCommandHandler';
import { FileCommandHandler } from './feature/files/FileCommandHandler';
import { HistoryManager } from './feature/chat/HistoryManager';
import { QrWebviewProvider } from './feature/connect/QrWebviewProvider';
import { FileSystemHelper } from './core/data/FileSystemHelper';
import { TerminalCommandHandler } from './feature/terminal/TerminalCommandHandler';

import * as fs from 'fs';
import * as path from 'path';

let outputChannel: vscode.OutputChannel;

function log(msg: string) {
  if (!outputChannel) return;
  const time = new Date().toISOString().split('T')[1].slice(0, -1);
  const line = `[${time}] ${msg}`;
  outputChannel.appendLine(line);
  try {
    fs.appendFileSync('/tmp/antimatter_debug.log', line + '\n');
  } catch (e) {}
}

export async function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel('Antimatter Bridge');
  log('Antimatter Bridge activating...');

  // 1. Data & State Managers (The ViewModels)
  const connectionManager = new ConnectionManager();
  const chatManager = new ChatStateManager();
  const fsHelper = new FileSystemHelper();
  
  // 2. Core Infrastructure
  const router = new MessageRouter();
  const tunnel = new CloudflareTunnel((msg) => connectionManager.broadcast(msg), log);
  const authHandler = new AuthHandler(context, connectionManager, log);
  await authHandler.init();
  const wss = new BridgeWebSocketServer(connectionManager, authHandler, router, tunnel, log);
  const brainWatcher = new BrainWatcher(chatManager, connectionManager, tunnel, log);
  const qrProvider = new QrWebviewProvider(log);

  // 3. Feature Handlers
  const chatHandler = new ChatCommandHandler(router, chatManager, log);
  const fileHandler = new FileCommandHandler(router, fsHelper, log);
  const historyManager = new HistoryManager(router, log);
  const terminalHandler = new TerminalCommandHandler(router, connectionManager, log);

  // 4. Register Routes
  router.register('AUTH_CHALLENGE', async (msg, ws) => {
    authHandler.handleAuthChallenge(ws, msg.challenge);
    
    // Add a small delay to give the Android client time to process the AUTH_RESPONSE
    // and transition its internal StateFlow to CONNECTED before we bombard it with state.
    setTimeout(() => {
      // Sync session state after auth
      ws.send(JSON.stringify({
        type: 'SESSION_STATE',
        conversationId: chatManager.getActiveConversation(),
        model: 'gemini-2.5-pro',
        stepCount: chatManager.getStepCount(),
        cloudflareUrl: tunnel.getUrl(),
        environment: 'IDE'
      }));
      
      // Push active file immediately
      const activeEditor = vscode.window.activeTextEditor;
      if (activeEditor) {
        ws.send(JSON.stringify({
          type: 'ACTIVE_FILE',
          path: activeEditor.document.uri.fsPath,
          language: activeEditor.document.languageId,
        }));
      }
    }, 500);
  });

  router.register('SUBSCRIBE_CONVERSATION', async (msg, ws) => {
    chatManager.setActiveConversation(msg.conversationId);
    brainWatcher.setConversation(msg.conversationId, msg.lastKnownStepCount || 0);
  });

  router.register('PING', async (msg, ws) => {
    ws.send(JSON.stringify({ type: 'PONG' }));
  });

  // Status bar item showing connection count
  const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = 'antimatter.showStatus';
  statusBarItem.text = '$(broadcast) Antimatter';
  statusBarItem.tooltip = 'Antimatter Bridge — click for status';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  const startBridge = async () => {
    const config = vscode.workspace.getConfiguration('antimatter');
    const port = config.get<number>('port', 8765);
    
    try {
      wss.start(port);
      await tunnel.start(port);
      brainWatcher.start();
      log('Bridge fully started.');
      vscode.window.showInformationMessage(`Antimatter Bridge running on port ${port}.`);
    } catch (e) {
      log(`Failed to start bridge: ${e}`);
    }
  };

  const stopBridge = () => {
    wss.stop();
    tunnel.stop();
    brainWatcher.stop();
    log('Bridge stopped.');
  };

  // 6. Register VS Code Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('antimatter.startBridge', startBridge),
    vscode.commands.registerCommand('antimatter.stopBridge', stopBridge),
    vscode.commands.registerCommand('antimatter.restartTunnel', async () => {
      const config = vscode.workspace.getConfiguration('antimatter');
      const port = config.get<number>('port', 8765);
      tunnel.stop();
      await tunnel.start(port);
      vscode.window.showInformationMessage('Antimatter Tunnel Restarted.');
    }),
    vscode.commands.registerCommand('antimatter.showStatus', () => {
      const url = tunnel.getUrl();
      if (url) {
        vscode.window.showInformationMessage(`Antimatter: Connected to ${url}`);
      } else {
        vscode.window.showInformationMessage('Antimatter: Tunnel not connected.');
      }
    }),
    vscode.commands.registerCommand('antimatter.showPairingQR', () => {
      const config = vscode.workspace.getConfiguration('antimatter');
      qrProvider.showPairingQR(
        tunnel.getUrl(), 
        authHandler.getPairingToken(), 
        authHandler.getPublicKeyRawBase64(),
        config.get<string>('cloudflareClientId', ''),
        config.get<string>('cloudflareClientSecret', '')
      );
    }),
    vscode.commands.registerCommand('antimatter.setCloudflareCredentials', async () => {
      const config = vscode.workspace.getConfiguration('antimatter');
      const clientId = await vscode.window.showInputBox({ prompt: 'Cloudflare Client ID' });
      if (clientId) await config.update('cloudflareClientId', clientId, true);
      const clientSecret = await vscode.window.showInputBox({ prompt: 'Cloudflare Client Secret', password: true });
      if (clientSecret) await config.update('cloudflareClientSecret', clientSecret, true);
      vscode.window.showInformationMessage('Cloudflare credentials saved globally.');
    })
  );

  // Watch active editor changes → stream to Android
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) {
        connectionManager.broadcast({
          type: 'ACTIVE_FILE',
          path: editor.document.uri.fsPath,
          language: editor.document.languageId,
        });
      }
    }),
  );

  // Auto-start if configured
  const config = vscode.workspace.getConfiguration('antimatter');
  if (config.get<boolean>('autoStart', true)) {
    startBridge();
  }

  log('Antimatter Bridge activated.');
}

export function deactivate() {
  // Not strictly necessary to export a real unmount since extension disposes properly
}
