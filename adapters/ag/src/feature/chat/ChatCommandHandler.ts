import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { MessageRouter } from '../../core/network/MessageRouter';
import { ChatStateManager } from '../../core/state/ChatStateManager';

export class ChatCommandHandler {
  constructor(
    private router: MessageRouter,
    private chatState: ChatStateManager,
    _log: (msg: string) => void  // retained for API consistency; not used in this handler
  ) {
    this.registerHandlers();
  }

  private brainPath = path.resolve(os.homedir(), '.gemini', 'antigravity-ide', 'brain');

  private registerHandlers() {
    this.router.register('SEND_MESSAGE', async (msg, _ws) => {
      let finalPrompt = msg.text;

      if (msg.images && msg.images.length > 0) {
        const cid = this.chatState.getActiveConversation();
        if (cid) {
          const scratchDir = path.join(this.brainPath, cid, 'scratch');
          if (!fs.existsSync(scratchDir)) {
            fs.mkdirSync(scratchDir, { recursive: true });
          }

          let imageMarkdown = '';
          for (let i = 0; i < msg.images.length; i++) {
            const imageData = msg.images[i];
            const base64Data = imageData.replace(/^data:image\/\w+;base64,/, '');
            
            const filename = `upload_${Date.now()}_${i}.jpg`;
            const filePath = path.join(scratchDir, filename);
            
            fs.writeFileSync(filePath, base64Data, 'base64');
            imageMarkdown += `![Image](file://${filePath})\n\n`;
          }
          finalPrompt = imageMarkdown + finalPrompt;
        }
      }

      await vscode.commands.executeCommand('antigravity.openAgent');
      await vscode.commands.executeCommand('antigravity.sendPromptToAgentPanel', finalPrompt);
    });

    this.router.register('NEW_CONVERSATION', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.startNewConversation');
      this.chatState.clearActiveConversation();
    });

    this.router.register('CANCEL_RESPONSE', async (_msg, _ws) => {
      await vscode.commands.executeCommand('workbench.action.chat.cancel');
    });

    this.router.register('CHANGE_MODEL', async (_msg, _ws) => {
      await vscode.commands.executeCommand('workbench.action.chat.openModelPicker');
    });

    this.router.register('ACCEPT_EDITS', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentAcceptAllInFile');
    });

    this.router.register('REJECT_EDITS', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentRejectAllInFile');
    });

    this.router.register('ACCEPT_HUNK', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentAcceptFocusedHunk');
    });

    this.router.register('REJECT_HUNK', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentRejectFocusedHunk');
    });

    this.router.register('NEXT_HUNK', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentFocusNextHunk');
    });

    this.router.register('PREV_HUNK', async (_msg, _ws) => {
      await vscode.commands.executeCommand('antigravity.prioritized.agentFocusPreviousHunk');
    });
  }
}
