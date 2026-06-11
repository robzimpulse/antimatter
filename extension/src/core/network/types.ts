export type InboundMessage =
  | { type: 'SEND_MESSAGE'; text: string }
  | { type: 'NEW_CONVERSATION' }
  | { type: 'CANCEL_RESPONSE' }
  | { type: 'ACCEPT_EDITS' }
  | { type: 'REJECT_EDITS' }
  | { type: 'NEXT_HUNK' }
  | { type: 'PREV_HUNK' }
  | { type: 'ACCEPT_HUNK' }
  | { type: 'REJECT_HUNK' }
  | { type: 'GET_FILES'; path?: string }
  | { type: 'READ_FILE'; path: string }
  | { type: 'WRITE_FILE'; path: string; content: string }
  | { type: 'SUBSCRIBE_CONVERSATION'; conversationId: string; lastKnownStepCount?: number }
  | { type: 'GET_HISTORY' }
  | { type: 'GET_ARTIFACTS'; conversationId: string }
  | { type: 'AUTH_CHALLENGE'; challenge: string }
  | { type: 'EXECUTE_COMMAND'; command: string }
  | { type: 'PING' };

export type OutboundMessage =
  | { type: 'PONG' }
  | { type: 'SESSION_STATE'; conversationId: string | null; model: string; stepCount: number; cloudflareUrl: string | null }
  | { type: 'STEP'; step: TrajectoryStep; index: number }
  | { type: 'STEP_BATCH'; steps: { step: TrajectoryStep; index: number }[] }
  | { type: 'GENERATING'; conversationId: string }
  | { type: 'RESPONSE_COMPLETE'; conversationId: string }
  | { type: 'ACTIVE_FILE'; path: string; language: string }
  | { type: 'FILE_CONTENT'; path: string; content: string; language: string }
  | { type: 'FILE_TREE'; tree: FileNode[] }
  | { type: 'CLOUDFLARE_URL'; url: string }
  | { type: 'HISTORY_LIST'; conversations: { id: string; timestamp: number; title: string }[] }
  | { type: 'ARTIFACTS_LIST'; artifacts: any[] }
  | { type: 'ERROR'; message: string }
  | { type: 'AUTH_RESPONSE'; signature: string }
  | { type: 'COMMAND_OUTPUT'; text: string; isError: boolean }
  | { type: 'SUCCESS'; message: string };

export interface TrajectoryStep {
  case: string;
  value?: string;
  tool?: string;
  command?: string;
  [key: string]: unknown;
}

export interface FileNode {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileNode[];
}
