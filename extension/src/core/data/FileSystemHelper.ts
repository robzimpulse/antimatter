import * as vscode from 'vscode';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';
import { FileNode } from '../network/types';

export class FileSystemHelper {
  private brainPath = path.resolve(os.homedir(), '.gemini', 'antigravity-ide', 'brain');

  isPathAllowed(targetPath: string, isWriteOperation: boolean): boolean {
    try {
      const resolvedPath = path.resolve(targetPath);
      
      // Rule 1: Allow Read/Write inside active VS Code Workspace folders
      if (vscode.workspace.workspaceFolders) {
        for (const folder of vscode.workspace.workspaceFolders) {
          const folderPath = path.resolve(folder.uri.fsPath);
          if (resolvedPath.startsWith(folderPath + path.sep) || resolvedPath === folderPath) {
            return true;
          }
        }
      }
      
      // Rule 2: Allow READ ONLY inside the Gemini Brain directory
      if (resolvedPath.startsWith(this.brainPath + path.sep) || resolvedPath === this.brainPath) {
        return !isWriteOperation; // Reject write operations to the brain directory
      }
      
      return false;
    } catch (e) {
      return false;
    }
  }

  async buildFileTree(dirPath: string, depth: number): Promise<FileNode[]> {
    if (depth === 0) return [];

    const IGNORED = new Set([
      'node_modules', '.git', 'dist', 'build', 'out', '.gradle',
      '__pycache__', '.venv', 'venv', '.idea', '.DS_Store',
    ]);

    try {
      const entries = fs.readdirSync(dirPath, { withFileTypes: true });
      const nodes: FileNode[] = [];

      for (const entry of entries) {
        if (IGNORED.has(entry.name)) continue;

        const fullPath = path.join(dirPath, entry.name);
        const node: FileNode = {
          name: entry.name,
          path: fullPath,
          isDir: entry.isDirectory(),
        };

        if (entry.isDirectory() && depth > 1) {
          node.children = await this.buildFileTree(fullPath, depth - 1);
        }

        nodes.push(node);
      }

      // Directories first, then files, alphabetical
      return nodes.sort((a, b) => {
        if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
    } catch {
      return [];
    }
  }
}
