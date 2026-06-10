import * as vscode from 'vscode';
import { MessageRouter } from '../../core/network/MessageRouter';
import { ChatStateManager } from '../../core/state/ChatStateManager';

export class ChatCommandHandler {
  constructor(
    private router: MessageRouter,
    private chatState: ChatStateManager,
    private log: (msg: string) => void
  ) {
    this.registerHandlers();
  }

  private registerHandlers() {
    this.router.register('SEND_MESSAGE', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.openAgent');
      await vscode.commands.executeCommand('antigravity.sendPromptToAgentPanel', msg.text);
    });

    this.router.register('NEW_CONVERSATION', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.startNewConversation');
      this.chatState.clearActiveConversation();
    });

    this.router.register('CANCEL_RESPONSE', async (msg, ws) => {
      await vscode.commands.executeCommand('workbench.action.chat.cancel');
    });

    this.router.register('CHANGE_MODEL', async (msg, ws) => {
      await vscode.commands.executeCommand('workbench.action.chat.openModelPicker');
    });

    this.router.register('ACCEPT_EDITS', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentAcceptAllInFile');
    });

    this.router.register('REJECT_EDITS', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentRejectAllInFile');
    });

    this.router.register('ACCEPT_HUNK', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentAcceptFocusedHunk');
    });

    this.router.register('REJECT_HUNK', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentRejectFocusedHunk');
    });

    this.router.register('NEXT_HUNK', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentFocusNextHunk');
    });

    this.router.register('PREV_HUNK', async (msg, ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentFocusPreviousHunk');
    });
  }
}
