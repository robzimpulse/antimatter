import { WebSocket } from 'ws';

export class ConnectionManager {
  private clients = new Set<WebSocket>();
  private authenticatedClients = new Set<WebSocket>();

  addClient(ws: WebSocket) {
    this.clients.add(ws);
  }

  removeClient(ws: WebSocket) {
    this.clients.delete(ws);
    this.authenticatedClients.delete(ws);
  }

  authenticateClient(ws: WebSocket) {
    if (this.clients.has(ws)) {
      this.authenticatedClients.add(ws);
    }
  }

  isAuthenticated(ws: WebSocket): boolean {
    return this.authenticatedClients.has(ws);
  }

  broadcast(message: any) {
    const payload = JSON.stringify(message);
    for (const client of this.authenticatedClients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(payload);
      }
    }
  }
}
