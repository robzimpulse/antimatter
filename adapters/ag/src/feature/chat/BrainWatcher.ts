import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { ConnectionManager } from '../../feature/connect/ConnectionManager';
import { ChatStateManager } from '../../core/state/ChatStateManager';
import { TrajectoryStep } from '../../core/network/types';

export class BrainWatcher {
  private brainPath = path.resolve(os.homedir(), '.gemini', 'antigravity-ide', 'brain');
  private activeWatcher: fs.FSWatcher | null = null;
  private rootWatcher: fs.FSWatcher | null = null;
  
  private lastReadBytes = 0;
  private tailBuffer = '';
  private debounceTimer: NodeJS.Timeout | null = null;

  constructor(
    private chatState: ChatStateManager,
    private connectionManager: ConnectionManager,
    private log: (msg: string) => void
  ) {}

  start() {
    if (!fs.existsSync(this.brainPath)) {
      try {
        fs.mkdirSync(this.brainPath, { recursive: true });
      } catch (e) {
        this.log(`Failed to create brain directory: ${e}`);
        return;
      }
    }

    // 1. Watch the root brain dir for new conversation folders
    this.rootWatcher = fs.watch(this.brainPath, (eventType, filename) => {
      if (filename && eventType === 'rename') {
        const fullPath = path.join(this.brainPath, filename);
        if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
          // Ignore tempmediaStorage and hidden folders
          if (filename === 'tempmediaStorage' || filename.startsWith('.')) return;
          this.checkForNewConversation(filename);
        }
      }
    });

    // 2. Do an initial scan to find the latest conversation
    this.scanForLatestConversation();
  }

  stop() {
    if (this.rootWatcher) this.rootWatcher.close();
    if (this.activeWatcher) this.activeWatcher.close();
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
  }

  private scanForLatestConversation() {
    const dirs = fs.readdirSync(this.brainPath, { withFileTypes: true });
    let latestDir = '';
    let latestTime = 0;

    for (const dir of dirs) {
      if (!dir.isDirectory() || dir.name === 'tempmediaStorage' || dir.name.startsWith('.')) continue;

      const transcriptPath = path.join(this.brainPath, dir.name, '.system_generated', 'logs', 'transcript.jsonl');
      if (fs.existsSync(transcriptPath)) {
        const stat = fs.statSync(transcriptPath);
        if (stat.mtimeMs > latestTime) {
          latestTime = stat.mtimeMs;
          latestDir = dir.name;
        }
      }
    }

    if (latestDir) {
      this.setConversation(latestDir);
    }
  }

  private checkForNewConversation(conversationId: string) {
    if (this.chatState.getActiveConversation() !== conversationId) {
      this.setConversation(conversationId);
    }
  }

  public setConversation(conversationId: string, clientLastKnownStepCount: number = 0) {

    
    // Close existing watcher
    if (this.activeWatcher) {
      this.activeWatcher.close();
      this.activeWatcher = null;
    }

    this.chatState.setActiveConversation(conversationId);
    this.chatState.resetStepCount();
    this.lastReadBytes = 0;
    this.tailBuffer = '';

    const transcriptPath = path.join(this.brainPath, conversationId, '.system_generated', 'logs', 'transcript.jsonl');

    // BUG-001: Polling fallback with a 60-second timeout (120 × 500ms) to prevent memory leak
    // if the transcript file never appears (e.g. AntiGravity crashed).
    let waitAttempts = 0;
    const MAX_WAIT_ATTEMPTS = 120;
    const waitForFile = setInterval(async () => {
      waitAttempts++;
      if (waitAttempts > MAX_WAIT_ATTEMPTS) {
        clearInterval(waitForFile);
        this.log(`[BrainWatcher] Timeout waiting for transcript: ${transcriptPath}`);
        return;
      }
      if (fs.existsSync(transcriptPath)) {
        clearInterval(waitForFile);
        
        // Initial read
        await this.processFile(transcriptPath, clientLastKnownStepCount);

        // Always broadcast SESSION_STATE after the initial read so stepCount is accurate
        this.connectionManager.broadcast({
          type: 'SESSION_STATE',
          conversationId,
          model: 'gemini-2.5-pro',
          stepCount: this.chatState.getStepCount(),
          cloudflareUrl: null,
          environment: 'IDE',
        });

        // Watch for changes
        this.activeWatcher = fs.watch(transcriptPath, (eventType) => {
          if (eventType === 'change') {
            // Debounce the fs.watch event (50ms) to prevent duplicate parsing
            if (this.debounceTimer) clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
              this.processFile(transcriptPath, 0);
            }, 50);
          }
        });
      }
    }, 500);
  }

  // STAB-001: Made async to use fs.promises instead of blocking synchronous I/O,
  // preventing the Node.js event loop from stalling on large transcript files.
  private async processFile(transcriptPath: string, clientLastKnownStepCount: number) {
    try {
      await fs.promises.access(transcriptPath);
    } catch {
      return;
    }

    try {
      const stat = await fs.promises.stat(transcriptPath);

    // File shrunk or was reset
    if (stat.size < this.lastReadBytes) {
      this.lastReadBytes = 0;
      this.chatState.resetStepCount();
    }

    if (stat.size > this.lastReadBytes) {
      const bufSize = stat.size - this.lastReadBytes;
      const buffer = Buffer.alloc(bufSize);
      const fh = await fs.promises.open(transcriptPath, 'r');
      try {
        await fh.read(buffer, 0, bufSize, this.lastReadBytes);
      } finally {
        await fh.close();
      }

      this.lastReadBytes = stat.size;

      const content = this.tailBuffer + buffer.toString('utf-8');
      const lines = content.split('\n');
      this.tailBuffer = lines.pop() || '';

      const newStepsBatch: { step: TrajectoryStep, index: number }[] = [];
      const completeLines = lines.filter(line => line.trim().length > 0);

      for (const line of completeLines) {
        try {
          const entry = JSON.parse(line);
          let stepValue = entry.content || '';
          let stepTool: string | undefined = undefined;
          let stepCommand: string | undefined = undefined;

          if (entry.type === 'USER_INPUT' && stepValue.includes('<USER_REQUEST>')) {
            const match = stepValue.match(/<USER_REQUEST>([\s\S]*?)<\/USER_REQUEST>/);
            if (match && match[1]) {
              stepValue = match[1].trim();
            }
          }

          if (entry.tool_calls && entry.tool_calls.length > 0) {
            const firstTool = entry.tool_calls[0];
            stepTool = firstTool.name;
            if (firstTool.args) {
              stepCommand = firstTool.args.CommandLine || firstTool.args.AbsolutePath || firstTool.args.query || firstTool.args.TargetFile || JSON.stringify(firstTool.args);
            }
          }

          if (entry.type === 'PLANNER_RESPONSE') {
            if (entry.thinking) {
              let cleanThinking = entry.thinking;
              cleanThinking = cleanThinking.split('\n\n').filter((paragraph: string) => {
                const p = paragraph.toLowerCase();
                const isBoilerplate = 
                    p.includes('critical instruction') ||
                    p.includes('tool specificity') ||
                    p.includes('tool usage') ||
                    p.includes('tool ecosystem') ||
                    p.includes('tool repertoire') ||
                    p.includes('instruction to avoid cat') ||
                    p.includes('eliminating the use of ls') ||
                    p.includes('default to grep_search') ||
                    p.includes('actively avoiding using ls') ||
                    p.includes('avoiding cat within bash') ||
                    p.includes('before making tool calls') ||
                    p.includes('list related tools') ||
                    p.includes('tool list: `') ||
                    p.includes('i must prioritize using the most specific tool') ||
                    (p.startsWith('#') && (p.includes('tool') || p.includes('instruction')));
                return !isBoilerplate;
              }).join('\n\n');
              
              // BUG-002: Rewrite filtering to avoid ESBuild minification array bugs
              const thinkingLines = cleanThinking.split('\n');
              let filteredThinking = '';
              for (const line of thinkingLines) {
                  const l = line.toLowerCase();
                  if (!l.includes('critical instruction') && !l.includes('tool specificity')) {
                      filteredThinking += line + '\n';
                  }
              }
              cleanThinking = filteredThinking.trim();

              const strippedOfPunctuation = cleanThinking.replace(/[#\s*\-=_]+/g, '').trim();
              if (strippedOfPunctuation.length > 0) {
                const thinkingStep: TrajectoryStep = {
                  case: 'PLANNER_RESPONSE',
                  value: cleanThinking,
                  tool: undefined,
                  command: undefined
                };
                newStepsBatch.push({ step: thinkingStep, index: this.chatState.getStepCount() });
                this.chatState.incrementStepCount();
              }
            }

            if (stepValue.trim() !== '') {
              const textStep: TrajectoryStep = {
                case: 'TEXT',
                value: stepValue,
                tool: undefined,
                command: undefined
              };
              newStepsBatch.push({ step: textStep, index: this.chatState.getStepCount() });
              this.chatState.incrementStepCount();
            }
            continue;
          }

          const step: TrajectoryStep = {
            case: entry.type,
            value: stepValue,
            tool: stepTool,
            command: stepCommand
          };

          newStepsBatch.push({ step, index: this.chatState.getStepCount() });
          this.chatState.incrementStepCount();
        } catch (e) {
          // Skip malformed JSON
        }
      }

      if (newStepsBatch.length > 0) {
        let filteredBatch = newStepsBatch;
        
        // If this batch corresponds to the start of the file
        if (newStepsBatch.length === this.chatState.getStepCount()) {
          if (clientLastKnownStepCount > 0) {
            if (this.chatState.getStepCount() >= clientLastKnownStepCount) {
              filteredBatch = newStepsBatch.filter(item => item.index >= clientLastKnownStepCount);
            } else {
              const syncFromIndex = Math.max(0, this.chatState.getStepCount() - 10);
              filteredBatch = newStepsBatch.filter(item => item.index >= syncFromIndex);
            }
          }
        }

        const CHUNK_SIZE = 10;
        for (let i = 0; i < filteredBatch.length; i += CHUNK_SIZE) {
          this.connectionManager.broadcast({ 
            type: 'STEP_BATCH', 
            steps: filteredBatch.slice(i, i + CHUNK_SIZE) 
          });
        }
      }
    }
    } catch (e) {
      this.log(`[BrainWatcher] processFile critical error: ${e}`);
      this.connectionManager.broadcast({ type: 'DEBUG_ERROR', message: `processFile failed: ${e}` });
    }
  }

  public async fetchHistoryPage(conversationId: string, offset: number, limit: number) {
    const transcriptPath = path.join(this.brainPath, conversationId, '.system_generated', 'logs', 'transcript.jsonl');
    try {
      await fs.promises.access(transcriptPath);
    } catch {
      return;
    }

    try {
      const content = await fs.promises.readFile(transcriptPath, 'utf8');
      const lines = content.split('\n').filter(l => l.trim().length > 0);
      const allSteps: { step: TrajectoryStep, index: number }[] = [];
      let currentIndex = 0;

      for (const line of lines) {
        try {
          const entry = JSON.parse(line);
          let stepValue = entry.content || '';
          let stepTool: string | undefined = undefined;
          let stepCommand: string | undefined = undefined;

          if (entry.type === 'USER_INPUT' && stepValue.includes('<USER_REQUEST>')) {
            const match = stepValue.match(/<USER_REQUEST>([\s\S]*?)<\/USER_REQUEST>/);
            if (match && match[1]) {
              stepValue = match[1].trim();
            }
          }

          if (entry.tool_calls && entry.tool_calls.length > 0) {
            const firstTool = entry.tool_calls[0];
            stepTool = firstTool.name;
            if (firstTool.args) {
              stepCommand = firstTool.args.CommandLine || firstTool.args.AbsolutePath || firstTool.args.query || firstTool.args.TargetFile || JSON.stringify(firstTool.args);
            }
          }

          if (entry.type === 'PLANNER_RESPONSE') {
            if (entry.thinking) {
              let cleanThinking = entry.thinking;
              const thinkingLines = cleanThinking.split('\n');
              let filteredThinking = '';
              for (const l of thinkingLines) {
                  const lower = l.toLowerCase();
                  if (!lower.includes('critical instruction') && !lower.includes('tool specificity')) {
                      filteredThinking += l + '\n';
                  }
              }
              cleanThinking = filteredThinking.trim();

              const strippedOfPunctuation = cleanThinking.replace(/[#\s*\-=_]+/g, '').trim();
              if (strippedOfPunctuation.length > 0) {
                allSteps.push({
                  step: { case: 'PLANNER_RESPONSE', value: cleanThinking, tool: undefined, command: undefined },
                  index: currentIndex++
                });
              }
            }

            if (stepValue.trim() !== '') {
              allSteps.push({
                step: { case: 'TEXT', value: stepValue, tool: undefined, command: undefined },
                index: currentIndex++
              });
            }
            continue;
          }

          allSteps.push({
            step: { case: entry.type, value: stepValue, tool: stepTool, command: stepCommand },
            index: currentIndex++
          });
        } catch (e) {
          // Skip malformed JSON
        }
      }

      const pageSteps = allSteps.slice(offset, offset + limit);
      const CHUNK_SIZE = 10;
      for (let i = 0; i < pageSteps.length; i += CHUNK_SIZE) {
        this.connectionManager.broadcast({ 
          type: 'STEP_BATCH', 
          steps: pageSteps.slice(i, i + CHUNK_SIZE) 
        });
      }
    } catch (e) {
      this.log(`[BrainWatcher] fetchHistoryPage error: ${e}`);
    }
  }
}
