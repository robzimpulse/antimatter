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
    this.router.register('GET_HISTORY', async (_msg, ws) => {
      try {
        const history = await this.getConversationHistory();

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

      
      try {
        try {
          await fs.promises.access(artifactsPath);
        } catch {
          ws.send(JSON.stringify({ type: 'ARTIFACTS_LIST', artifacts: [] }));
          return;
        }

        const entries = await fs.promises.readdir(artifactsPath, { withFileTypes: true });
        const artifacts: any[] = [];
        const allowedExtensions = ['.md', '.csv', '.txt', '.json'];
        for (const entry of entries) {
          if (entry.isFile() && allowedExtensions.some(ext => entry.name.toLowerCase().endsWith(ext))) {
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

    this.router.register('READ_ARTIFACT', async (msg, ws) => {
      const { conversationId, path: artifactPath } = msg;
      if (!conversationId || !/^[a-zA-Z0-9-]+$/.test(conversationId)) {
        ws.send(JSON.stringify({ type: 'ERROR', message: 'Invalid or missing conversation ID' }));
        return;
      }
      if (!artifactPath) {
        ws.send(JSON.stringify({ type: 'ERROR', message: 'Missing artifact path' }));
        return;
      }

      // Security: ensure the requested path is actually inside the conversation's brain directory
      const baseDir = path.resolve(path.join(this.brainDir, conversationId));
      const targetPath = path.resolve(artifactPath);
      if (!targetPath.startsWith(baseDir)) {
        ws.send(JSON.stringify({ type: 'ERROR', message: 'Path traversal rejected: Artifact is outside conversation directory' }));
        return;
      }

      try {
        const content = await fs.promises.readFile(targetPath, 'utf8');
        ws.send(JSON.stringify({
          type: 'ARTIFACT_CONTENT',
          path: targetPath,
          content: content,
          language: path.extname(targetPath).substring(1) || 'text'
        }));
      } catch (err) {
        this.log(`READ_ARTIFACT Error: ${err}`);
        ws.send(JSON.stringify({ type: 'ERROR', message: `Could not read artifact: ${err}` }));
      }
    });
  }

  private async getConversationHistory(): Promise<{ id: string; timestamp: number; title: string }[]> {
    if (!fs.existsSync(this.brainDir)) return [];

    const history: { id: string; timestamp: number; title: string }[] = [];
    const dirs = fs.readdirSync(this.brainDir, { withFileTypes: true });
    
    // Lazy load readline to avoid global imports if not needed
    const readline = require('readline');

    for (const dir of dirs) {
      if (!dir.isDirectory() || dir.name.startsWith('.') || dir.name === 'tempmediaStorage') continue;

      const transcriptPath = path.join(this.brainDir, dir.name, '.system_generated', 'logs', 'transcript.jsonl');
      if (!fs.existsSync(transcriptPath)) continue;

      const stat = fs.statSync(transcriptPath);
      let title = 'New Conversation';

      try {
        const fileStream = fs.createReadStream(transcriptPath);
        const rl = readline.createInterface({
          input: fileStream,
          crlfDelay: Infinity
        });

        for await (const line of rl) {
          if (!line.trim()) continue;
          try {
            const entry = JSON.parse(line);
            if (entry.type === 'USER_INPUT' && entry.content) {
              let text = entry.content;
              if (text.includes('<USER_REQUEST>')) {
                const match = text.match(/<USER_REQUEST>([\s\S]*?)<\/USER_REQUEST>/);
                if (match && match[1]) text = match[1].trim();
              } else {
                text = text.replace(/<[^>]+>/g, '').trim();
              }
              title = text.length > 50 ? text.substring(0, 50) + '...' : text;
              break;
            }
          } catch { }
        }
        
        rl.close();
        fileStream.destroy();
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
