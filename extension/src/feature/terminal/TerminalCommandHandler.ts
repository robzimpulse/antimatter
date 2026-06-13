import { spawn } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';
import { MessageRouter } from '../../core/network/MessageRouter';
import { ConnectionManager } from '../connect/ConnectionManager';

const AUDIT_LOG_PATH = path.join(os.tmpdir(), 'antimatter_terminal_audit.log');

// VULN-V2-001: Allowlist of safe command patterns
const ALLOWED_COMMANDS: RegExp[] = [
  /^npm\s+/,
  /^yarn\s+/,
  /^pnpm\s+/,
  /^git\s+/,
  /^ls(\s|$)/,
  /^cat\s+/,
  /^pwd$/,
  /^echo\s+/,
  /^mkdir\s+/,
  /^touch\s+/,
  /^cp\s+/,
  /^mv\s+/,
  /^grep\s+/,
  /^find\s+/,
  /^which\s+/,
  /^env$/,
  /^node\s+/,
  /^python3?\s+/,
  /^pip3?\s+/,
  /^gradlew?\s+/,
  /^make\s+/,
];

// VULN-V2-001: Explicit denylist for dangerous command patterns
const DANGEROUS_PATTERNS: RegExp[] = [
  /\brm\s+-[rf]+/,
  /\bsudo\b/,
  /\bchmod\b/,
  /\bchown\b/,
  /\bmkfs\b/,
  /\bdd\b/,
  /\bformat\b/,
  /\bshutdown\b/,
  /\breboot\b/,
  /\b(crontab|at)\b/,
  /;|\|\||&&|`|\$\(/,  // Shell injection operators
];

function isCommandAllowed(command: string): boolean {
  const cmd = command.trim();
  if (DANGEROUS_PATTERNS.some(p => p.test(cmd))) {
    return false;
  }
  return ALLOWED_COMMANDS.some(p => p.test(cmd));
}

function isDangerous(command: string): boolean {
  return DANGEROUS_PATTERNS.some(p => p.test(command.trim()));
}

function appendAuditLog(command: string, allowed: boolean, exitCode: number | null) {
  try {
    const timestamp = new Date().toISOString();
    const status = exitCode !== null ? `exit=${exitCode}` : 'blocked';
    const entry = `[${timestamp}] ${allowed ? 'EXEC' : 'BLOCKED'} (${status}): ${command}\n`;
    fs.appendFileSync(AUDIT_LOG_PATH, entry, 'utf-8');
  } catch {
    // Non-fatal: audit log write failure should not break terminal
  }
}

export class TerminalCommandHandler {
  constructor(
    private router: MessageRouter,
    private connectionManager: ConnectionManager,
    private log: (msg: string) => void
  ) {
    this.registerHandlers();
  }

  private registerHandlers() {
    this.router.register('EXECUTE_COMMAND', async (msg, ws) => {
      this.log(`Executing command: ${msg.command}`);
      const cmdTrimmed = msg.command.trim();

      // VULN-V2-001: Check denylist first, then allowlist
      if (isDangerous(cmdTrimmed)) {
        this.log(`Command rejected by denylist (dangerous): ${msg.command}`);
        appendAuditLog(msg.command, false, null);
        this.connectionManager.broadcast({
          type: 'COMMAND_OUTPUT',
          text: `Error: Command contains dangerous pattern and is not permitted.\n`,
          isError: true
        });
        return;
      }

      if (!isCommandAllowed(cmdTrimmed)) {
        this.log(`Command rejected by allowlist: ${msg.command}`);
        appendAuditLog(msg.command, false, null);
        this.connectionManager.broadcast({
          type: 'COMMAND_OUTPUT',
          text: `Error: Command not in allowlist. Allowed: npm, yarn, git, ls, cat, pwd, echo, mkdir, touch, cp, mv, grep, find, node, python, pip, gradle, make.\n`,
          isError: true
        });
        return;
      }

      try {
        const shell = process.platform === 'win32' ? 'cmd.exe' : '/bin/sh';
        const args = process.platform === 'win32' ? ['/c', msg.command] : ['-c', msg.command];
        
        const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
        const child = spawn(shell, args, { cwd });
        
        const TIMEOUT_MS = 5 * 60 * 1000;
        const timeoutTimer = setTimeout(() => {
          child.kill('SIGTERM');
          this.connectionManager.broadcast({
            type: 'COMMAND_OUTPUT',
            text: `\n[Process terminated due to 5-minute timeout]\n`,
            isError: true
          });
        }, TIMEOUT_MS);
        
        child.stdout.on('data', (data) => {
          this.connectionManager.broadcast({
            type: 'COMMAND_OUTPUT',
            text: data.toString(),
            isError: false
          });
        });
        
        child.stderr.on('data', (data) => {
          this.connectionManager.broadcast({
            type: 'COMMAND_OUTPUT',
            text: data.toString(),
            isError: true
          });
        });
        
        child.on('close', (code) => {
          clearTimeout(timeoutTimer);
          appendAuditLog(msg.command, true, code);
          this.connectionManager.broadcast({
            type: 'COMMAND_OUTPUT',
            text: `\n[Process exited with code ${code}]\n`,
            isError: code !== 0
          });
        });
        
        child.on('error', (err) => {
          clearTimeout(timeoutTimer);
          this.log(`Failed to start command: ${err.message}`);
          this.connectionManager.broadcast({
            type: 'COMMAND_OUTPUT',
            text: `Failed to start process: ${err.message}\n`,
            isError: true
          });
        });
      } catch (err: any) {
        this.log(`Error executing command: ${err.message}`);
        this.connectionManager.broadcast({
          type: 'COMMAND_OUTPUT',
          text: `Execution error: ${err.message}\n`,
          isError: true
        });
      }
    });
  }
}
