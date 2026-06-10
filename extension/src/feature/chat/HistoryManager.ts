import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { MessageRouter } from '../../core/network/MessageRouter';

export class HistoryManager {
  private brainDir = path.join(os.homedir(), '.gemini', 'antigravity-ide', 'brain');

  constructor(
    private router: MessageRouter,
    private log: (msg: string) => void
  ) {
    this.registerHandlers();
  }

  private registerHandlers() {
    this.router.register('GET_HISTORY', async (msg, ws) => {
      try {
        const history = await this.getConversationHistory();
        this.log(`→ HISTORY_LIST with ${history.length} items`);
        ws.send(JSON.stringify({ type: 'HISTORY_LIST', conversations: history }));
      } catch (err) {
        this.log(`GET_HISTORY Error: ${err}`);
        ws.send(JSON.stringify({ type: 'ERROR', message: 'Failed to fetch history' }));
      }
    });

    this.router.register('GET_ARTIFACTS', async (msg, ws) => {
      const conversationId = msg.conversationId;
      if (!conversationId || !/^[a-zA-Z0-9-]+$/.test(conversationId)) {
        ws.send(JSON.stringify({ type: 'ERROR', message: 'Invalid or missing conversation ID' }));
        return;
      }
      
      const artifactsPath = path.join(this.brainDir, conversationId);
      this.log(`GET_ARTIFACTS requested for conversation: ${conversationId}`);
      
      try {
        try {
          await fs.promises.access(artifactsPath);
        } catch {
          ws.send(JSON.stringify({ type: 'ARTIFACTS_LIST', artifacts: [] }));
          return;
        }

        const entries = await fs.promises.readdir(artifactsPath, { withFileTypes: true });
        const artifacts: any[] = [];
        for (const entry of entries) {
          if (entry.isFile() && entry.name.endsWith('.md')) {
            artifacts.push({
              name: entry.name,
              path: path.join(artifactsPath, entry.name),
              isDir: false,
            });
          }
        }
        ws.send(JSON.stringify({ type: 'ARTIFACTS_LIST', artifacts }));
      } catch (err) {
        this.log(`GET_ARTIFACTS Error: ${err}`);
        ws.send(JSON.stringify({ type: 'ERROR', message: `Cannot read artifacts for ${conversationId}` }));
      }
    });
  }

  private async getConversationHistory(): Promise<{ id: string; timestamp: number; title: string }[]> {
    if (!fs.existsSync(this.brainDir)) return [];

    const history: { id: string; timestamp: number; title: string }[] = [];
    const dirs = fs.readdirSync(this.brainDir, { withFileTypes: true });

    for (const dir of dirs) {
      if (!dir.isDirectory() || dir.name.startsWith('.') || dir.name === 'tempmediaStorage') continue;

      const transcriptPath = path.join(this.brainDir, dir.name, '.system_generated', 'logs', 'transcript.jsonl');
      if (!fs.existsSync(transcriptPath)) continue;

      const stat = fs.statSync(transcriptPath);
      let title = 'New Conversation';

      try {
        const fd = fs.openSync(transcriptPath, 'r');
        const buffer = Buffer.alloc(4096);
        const bytesRead = fs.readSync(fd, buffer, 0, 4096, 0);
        fs.closeSync(fd);

        const content = buffer.toString('utf-8', 0, bytesRead);
        const lines = content.split('\n');
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const entry = JSON.parse(line);
            if (entry.type === 'USER_INPUT' && entry.content) {
              let text = entry.content;
              if (text.includes('<USER_REQUEST>')) {
                const match = text.match(/<USER_REQUEST>([\s\S]*?)<\/USER_REQUEST>/);
                if (match && match[1]) text = match[1].trim();
              }
              title = text.length > 50 ? text.substring(0, 50) + '...' : text;
              break;
            }
          } catch { }
        }
      } catch { }

      history.push({
        id: dir.name,
        timestamp: Math.floor(stat.mtimeMs),
        title
      });
    }

    return history.sort((a, b) => b.timestamp - a.timestamp);
  }
}
