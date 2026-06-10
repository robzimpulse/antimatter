import { spawn } from 'child_process';
import * as vscode from 'vscode';
import { MessageRouter } from '../../core/network/MessageRouter';
import { ConnectionManager } from '../connect/ConnectionManager';

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
      
      try {
        const shell = process.platform === 'win32' ? 'cmd.exe' : '/bin/sh';
        const args = process.platform === 'win32' ? ['/c', msg.command] : ['-c', msg.command];
        
        const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
        const child = spawn(shell, args, { cwd });
        
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
          this.connectionManager.broadcast({
            type: 'COMMAND_OUTPUT',
            text: `\n[Process exited with code ${code}]\n`,
            isError: code !== 0
          });
        });
        
        child.on('error', (err) => {
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
