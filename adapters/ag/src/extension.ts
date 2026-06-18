import * as vscode from 'vscode';
import { ConnectionManager } from './feature/connect/ConnectionManager';
import { ChatStateManager } from './core/state/ChatStateManager';
import { MessageRouter } from './core/network/MessageRouter';
import { GatewayClient } from './core/network/GatewayClient';
import { BrainWatcher } from './feature/chat/BrainWatcher';
import { ChatCommandHandler } from './feature/chat/ChatCommandHandler';
import { FileCommandHandler } from './feature/files/FileCommandHandler';
import { HistoryManager } from './feature/chat/HistoryManager';
import { FileSystemHelper } from './core/data/FileSystemHelper';

let outputChannel: vscode.OutputChannel;

function log(msg: string) {
  if (!outputChannel) return;
  const time = new Date().toISOString().split('T')[1].slice(0, -1);
  const line = `[${time}] ${msg}`;
  outputChannel.appendLine(line);
}

export async function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel('Antimatter Adapter');
  log('Antimatter Adapter activating...');

  // 1. Data & State Managers
  const connectionManager = new ConnectionManager();
  const chatManager = new ChatStateManager();
  const fsHelper = new FileSystemHelper();
  
  // 2. Core Infrastructure (IPC to Gateway)
  const router = new MessageRouter();
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
  const gatewayClient = new GatewayClient(connectionManager, router, workspaceRoot, log);
  const brainWatcher = new BrainWatcher(chatManager, connectionManager, log);

  // 3. Feature Handlers
  new ChatCommandHandler(router, chatManager, log);
  new FileCommandHandler(router, fsHelper, log);
  new HistoryManager(router, log);

  router.register('SUBSCRIBE_CONVERSATION', async (msg, _ws) => {
    chatManager.setActiveConversation(msg.conversationId);
    brainWatcher.setConversation(msg.conversationId, msg.lastKnownStepCount || 0);
  });

  router.register('FETCH_HISTORY_PAGE', async (msg, _ws) => {
    await brainWatcher.fetchHistoryPage(msg.conversationId, msg.offset, msg.limit);
  });

  router.register('PING', async (_msg, _ws) => {
    // Gateway will handle generic PINGs, but we can reply if it routes it here
    connectionManager.broadcast({ type: 'PONG' });
  });

  const startAdapter = async () => {
    try {
      gatewayClient.start();
      brainWatcher.start();
      log('Adapter connected to Gateway IPC.');
      vscode.window.showInformationMessage(`Antimatter Adapter started.`);
    } catch (e) {
      log(`Failed to start adapter: ${e}`);
    }
  };

  const stopAdapter = () => {
    gatewayClient.stop();
    brainWatcher.stop();
    log('Adapter stopped.');
  };

  // 6. Register VS Code Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('antimatter.startAdapter', startAdapter),
    vscode.commands.registerCommand('antimatter.stopAdapter', stopAdapter),
    vscode.commands.registerCommand('antimatter.showConnectionInfo', () => {
      vscode.window.showInformationMessage('Pairing and connection info is managed by the Antimatter Gateway terminal. Run "antimatter qr" or "antimatter status" in your terminal.');
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

  // Auto-start
  const config = vscode.workspace.getConfiguration('antimatter');
  if (config.get<boolean>('autoStart', true)) {
    startAdapter();
  }

  log('Antimatter Adapter activated.');
}

export function deactivate() {
}
