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

// --- Voice mode API function ---
export interface VoiceResponse {
  text: string;
  audioUrl?: string;
}

export async function sendVoiceToAgent(
  audioBlob: Blob,
  hintText?: string
): Promise<VoiceResponse> {
  const sessionId = getOrCreateSessionId();
  const traceId = crypto.randomUUID();

  // Convert Blob to base64
  const arrayBuffer = await audioBlob.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);
  let binary = '';
  for (let i = 0; i < uint8Array.length; i++) {
    binary += String.fromCharCode(uint8Array[i]);
  }
  const base64Audio = btoa(binary);

  const payload: AgentChatRequest = {
    sessionId,
    message: hintText,
    audio: {
      mimeType: audioBlob.type || 'audio/webm',
      data: base64Audio,
    },
    voiceMode: true,
    client: { traceId },
  };

  logger.debug('agent-client', 'Sending voice request', {
    sessionId,
    traceId,
    audioSize: audioBlob.size,
    mimeType: audioBlob.type,
  });

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
      logger.error('agent-client', 'Voice HTTP error', {
        status: res.status,
        sessionId,
        traceId,
        error: err,
      });
      return {
        text: 'Przepraszam, wystąpił problem z połączeniem. Spróbuj ponownie.',
      };
    }

    const data: AgentChatResponse = await res.json();
    logger.info('agent-client', 'Voice response received', {
      sessionId,
      language: data.language,
      traceId,
      hasAudio: !!data.audio,
    });

    // Decode audio response if present
    let audioUrl: string | undefined;
    if (data.audio?.data) {
      try {
        const audioBytes = Uint8Array.from(atob(data.audio.data), (c) =>
          c.charCodeAt(0)
        );
        const audioBlob = new Blob([audioBytes], { type: data.audio.mimeType });
        audioUrl = URL.createObjectURL(audioBlob);
        logger.debug('agent-client', 'Audio URL created', {
          mimeType: data.audio.mimeType,
          blobSize: audioBlob.size,
        });
      } catch (e) {
        logger.error('agent-client', 'Failed to decode audio response', {
          error: e instanceof Error ? e.message : String(e),
        });
      }
    }

    return {
      text: data.reply,
      audioUrl,
    };
  } catch (e) {
    logger.error('agent-client', 'Voice network error', {
      sessionId,
      traceId,
      error: e instanceof Error ? e.message : String(e),
    });
    return {
      text: 'Przepraszam, nie udało się połączyć z concierge. Spróbuj za chwilę.',
    };
  }
}

// --- Utility: reset session (opcjonalne, dla debugowania) ---
export function resetSession(): void {
  localStorage.removeItem(SESSION_KEY);
  logger.info('agent-client', 'Session reset');
}
