/**
 * Agent API Client
 * Zastępuje bezpośrednie wywołania Gemini SDK na HTTP client do backendu /agent/chat
 */

import { logger } from './logger';
import type { AgentChatRequest, AgentChatResponse } from '../types';

// --- Config from env ---
const AGENT_API_BASE_URL =
  import.meta.env.VITE_AGENT_API_BASE_URL ?? 'http://localhost:8000';
const AGENT_JWT = import.meta.env.VITE_AGENT_JWT as string | undefined;

// --- Session management ---
const SESSION_KEY = 'gh_agent_session_id';

function getOrCreateSessionId(): string {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
    logger.info('agent-client', 'New session created', { sessionId: id });
  }
  return id;
}

// --- Main API function (zachowana sygnatura dla kompatybilności z UI) ---
export async function sendMessageToGemini(prompt: string): Promise<string> {
  const sessionId = getOrCreateSessionId();
  const traceId = crypto.randomUUID();

  const payload: AgentChatRequest = {
    sessionId,
    message: prompt,
    voiceMode: false,
    client: { traceId },
  };

  logger.debug('agent-client', 'Sending request', { sessionId, traceId, prompt });

  try {
    const res = await fetch(`${AGENT_API_BASE_URL}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(AGENT_JWT ? { Authorization: `Bearer ${AGENT_JWT}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      logger.error('agent-client', 'HTTP error', {
        status: res.status,
        sessionId,
        traceId,
        error: err,
      });
      return 'Przepraszam, wystąpił problem z połączeniem. Spróbuj ponownie.';
    }

    const data: AgentChatResponse = await res.json();
    logger.info('agent-client', 'Response received', {
      sessionId,
      language: data.language,
      traceId,
    });

    return data.reply;
  } catch (e) {
    logger.error('agent-client', 'Network error', {
      sessionId,
      traceId,
      error: e instanceof Error ? e.message : String(e),
    });
    return 'Przepraszam, nie udało się połączyć z concierge. Spróbuj za chwilę.';
  }
}

// --- Utility: reset session (opcjonalne, dla debugowania) ---
export function resetSession(): void {
  localStorage.removeItem(SESSION_KEY);
  logger.info('agent-client', 'Session reset');
}
