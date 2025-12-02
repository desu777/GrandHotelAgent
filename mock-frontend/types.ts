export interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: number;
}

export enum ChatModel {
  CONCIERGE = 'Grand Concierge',
  BOOKING = 'Asystent Rezerwacji',
}

// --- Agent API Types ---

export interface AudioPayload {
  mimeType: string;
  data: string; // base64
}

export interface AgentChatRequest {
  sessionId: string;
  message?: string;
  audio?: AudioPayload;
  voiceMode: boolean;
  client?: { traceId: string };
}

export interface AgentChatResponse {
  sessionId: string;
  language: string;
  reply: string;
  audio?: { mimeType: string; data: string };
  toolTrace?: Array<{ name: string; status: string; durationMs: number }>;
}

export interface AgentErrorResponse {
  code: string;
  message: string;
  status: number;
  traceId?: string;
}
