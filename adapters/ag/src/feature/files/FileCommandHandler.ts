import * as vscode from 'vscode';

import { FileSystemHelper } from '../../core/data/FileSystemHelper';
import { MessageRouter } from '../../core/network/MessageRouter';

export class FileCommandHandler {
  constructor(
    private router: MessageRouter,
    private fsHelper: FileSystemHelper,
    private log: (msg: string) => void
  ) {
    this.registerHandlers();
  }

  private registerHandlers() {
    this.router.register('GET_FILES', async (msg, ws) => {
      const rootPath = msg.path
        ? vscode.Uri.file(msg.path)
        : vscode.workspace.workspaceFolders?.[0]?.uri;
      
      if (!rootPath) {
        ws.send(JSON.stringify({ type: 'ERROR', message: 'No workspace folder open' }));
        return;
      }

      if (!this.fsHelper.isPathAllowed(rootPath.fsPath, false)) {
        ws.send(JSON.stringify({ type: 'ERROR', message: 'Unauthorized path' }));
        this.log(`Unauthorized GET_FILES requested for path: ${rootPath.fsPath}`);
        return;
      }


      try {
        const tree = await this.fsHelper.buildFileTree(rootPath.fsPath, 2);
        const payload = JSON.stringify({ type: 'FILE_TREE', tree });

        ws.send(payload);
      } catch (err) {
        this.log(`GET_FILES Error: ${err}`);
        ws.send(JSON.stringify({ type: 'ERROR', message: `Cannot list files in ${rootPath.fsPath}` }));
      }
    });

    this.router.register('READ_FILE', async (msg, ws) => {
      if (!this.fsHelper.isPathAllowed(msg.path, false)) {
        ws.send(JSON.stringify({ type: 'ERROR', message: `Unauthorized read path: ${msg.path}` }));
        this.log(`Unauthorized READ_FILE requested for path: ${msg.path}`);
        return;
      }
      try {
        const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(msg.path));
        ws.send(JSON.stringify({
          type: 'FILE_CONTENT',
          path: msg.path,
          content: doc.getText(),
          language: doc.languageId,
        }));
      } catch (err) {
        ws.send(JSON.stringify({ type: 'ERROR', message: `Cannot read file: ${msg.path}` }));
      }
    });

    this.router.register('WRITE_FILE', async (msg, ws) => {
      if (!this.fsHelper.isPathAllowed(msg.path, true)) { // isWriteOperation = true
        ws.send(JSON.stringify({ type: 'ERROR', message: `Unauthorized write path: ${msg.path}` }));
        this.log(`Unauthorized WRITE_FILE requested for path: ${msg.path}`);
        return;
      }
      if (Buffer.byteLength(msg.content, 'utf8') > 10 * 1024 * 1024) { // 10 MB Limit
        ws.send(JSON.stringify({ type: 'ERROR', message: `File too large` }));
        this.log(`Oversized WRITE_FILE requested for path: ${msg.path}`);
        return;
      }
      try {
        const uri = vscode.Uri.file(msg.path);
        await vscode.workspace.fs.writeFile(uri, Buffer.from(msg.content, 'utf8'));
        ws.send(JSON.stringify({ type: 'SUCCESS', message: `File saved: ${msg.path}` }));
      } catch (err) {
        ws.send(JSON.stringify({ type: 'ERROR', message: `Cannot write file: ${msg.path}` }));
      }
    });
  }
}
