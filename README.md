# GrandHotel Agent — Unified API 

## DOCS:
- https://ai.google.dev/gemini-api/docs/function-calling?hl=pl&example=meeting#javascript_2
- https://ai.google.dev/gemini-api/docs/models?hl=pl#gemini-2.5-flash_1



## 1) Overview
- One endpoint for all turns: `POST /agent/chat`; health: `GET /agent/health`.
- Model: `gemini-2.5-flash` + Function Calling (FC).
- Optional TTS via ElevenLabs when `voiceMode=true`.
- No WebSockets/SSE in v1.

## 2) Auth & Sessions
- `/agent/chat` requires `Authorization: Bearer <JWT>`; trust `sub/role/given_name`; forward JWT to backend.
- Frontend generates `sessionId` (UUID v4) before the first call and includes it on every request.
- Agent auto‑creates a session in Redis when it first sees a `sessionId`; sliding TTL = 60 minutes (refreshed on each turn). New conversation = new `sessionId`.
- Optional warmup: if JWT lacks display name, Agent may call backend `/api/v1/me` once to cache it.

## 3) Rate limiting
- 30 requests per minute per `sessionId`. On exceed: HTTP 429 with `{ code: "RATE_LIMITED", retryAfter: <seconds> }`.

## 4) Endpoints
### 4.1 `GET /agent/health` (public)
- 200 OK
```json
{ "status": "ok", "version": "1.0.0" }
```

### 4.2 `POST /agent/chat`
Headers
- `Authorization: Bearer <JWT>`
- `Content-Type: application/json`
- `Accept: application/json` (default) OR `audio/mpeg` (when `voiceMode=true` and client wants raw audio)

Request body (one of `message` or `audio` required; both allowed — `message` is a text hint alongside audio)
```json
{
  "sessionId": "uuid-v4",
  "message": "optional user text",
  "audio": { "mimeType": "audio/wav|audio/mp3|audio/aiff|audio/aac|audio/ogg|audio/flac", "data": "<base64>" },
  "voiceMode": false,
  "client": { "traceId": "optional <=64" }
}
```
Notes
- Inline total request size (text+audio+system) must be ≤ 20 MB (Gemini REST limit). Larger audio can use Files API in a later version.
- Processing pipeline: Agent builds prompt (system + short session summary + optional displayName + current input), enables thinking, attaches FC `functionDeclarations`, calls `gemini-2.5-flash`.
- If model returns `functionCall{name,args}`: validate (Zod), call GrandHotelBackend with JWT, send `functionResponse`, then produce the final text.
- If `voiceMode=true`: synthesize TTS with ElevenLabs (`mp3_44100_128`) and attach to response.

200 OK (JSON)
```json
{
  "sessionId": "uuid-v4",
  "language": "en-US",
  "reply": "Final answer",
  "audio": { "mimeType": "audio/mpeg", "data": "<base64>" },
  "toolTrace": [ { "name": "rooms_filter", "status": "OK", "durationMs": 142 } ]
}
```
- Omit `audio` when `voiceMode=false`; `toolTrace` optional.

200 OK (audio body)
- If `Accept: audio/mpeg` AND `voiceMode=true` → body is raw MP3 bytes; headers include `X-Agent-Text: <url-escaped final text>`.

Errors (unified envelope)
```json
{ "code": "STRING_CONST", "message": "Human readable", "status": 400, "traceId": "optional", "details": { "field": "context" } }
```
- Common: 400 BAD_REQUEST (invalid input/unsupported mime), 413 PAYLOAD_TOO_LARGE (inline >20MB), 401/403 auth, 422 UNPROCESSABLE_ENTITY (business rules), 429 RATE_LIMITED, 500 INTERNAL_ERROR, 502 BACKEND_5XX.

## 5) Function Calling — tools → backend
- `rooms_list {}`                        → GET `/api/v1/rooms`
- `rooms_get { id:int }`                 → GET `/api/v1/rooms/{id}`
- `rooms_filter { checkInDate, checkOutDate, numberOfAdults:int>=1, numberOfChildren:int>=0 }` → POST `/api/v1/rooms/filter`
- `reservations_create { checkInDate, checkOutDate, numberOfAdults, numberOfChildren, roomId:int }` → POST `/api/v1/reservations`
- `reservations_get { id:int }`          → GET `/api/v1/reservations/{id}`
- `reservations_list {}`                 → GET `/api/v1/reservations`
- `reservations_update { id:int, checkInDate?, checkOutDate?, numberOfAdults?, numberOfChildren?, status? }` → PUT `/api/v1/reservations/{id}`
- `reservations_cancel { id:int }`       → DELETE `/api/v1/reservations/{id}`
- `restaurant_menu {}`                   → GET `/api/v1/restaurant/menu`
- `restaurant_table_create { date:YYYY-MM-DD, time:HH:MM, guests:int }` → POST `/api/v1/restaurant/reservations`
- `restaurant_table_get { id:int }`      → GET `/api/v1/restaurant/reservations/{id}`
- `restaurant_table_list {}`             → GET `/api/v1/restaurant/reservations`
- `restaurant_table_update { id:int, date?, time?, guests?, status? }` → PUT `/api/v1/restaurant/reservations/{id}`
- `restaurant_table_cancel { id:int }`   → DELETE `/api/v1/restaurant/reservations/{id}`

## 6) Privacy
- Only first name sent to the model; do not send emails/phones/IDs.
- No raw audio persisted; short transcript/summary kept in Redis for the session TTL only.

## 7) Examples
Text request
```http
POST /agent/chat
Authorization: Bearer <JWT>
Content-Type: application/json
Accept: application/json

{"sessionId":"b1d6c0f0-4a1d-4e3c-9b23-6e7c1c8a2f01","message":"Room for 3 on Oct 24–27","voiceMode":false}
```

Audio request
```http
POST /agent/chat
Authorization: Bearer <JWT>
Content-Type: application/json
Accept: application/json

{"sessionId":"b1d6c0f0-4a1d-4e3c-9b23-6e7c1c8a2f01","audio":{"mimeType":"audio/mp3","data":"<base64>"},"voiceMode":true}
```

## 8) Voice mode responses (TTS via ElevenLabs)
- When `voiceMode=true`, the Agent first gets the final text from Gemini, then calls ElevenLabs Text‑to‑Speech and returns audio in one of two formats.

1) JSON (default)
- 200 OK
```json
{
  "sessionId": "uuid-v4",
  "language": "en-US",
  "reply": "Final answer",
  "audio": { "mimeType": "audio/mpeg", "data": "<base64 MP3>" },
  "toolTrace": [ { "name": "rooms_filter", "status": "OK", "durationMs": 142 } ]
}
```
- Notes: `reply` is always present for UI; omit `audio` if TTS fails and include
```json
{ "warnings": [ { "code": "TTS_UNAVAILABLE", "message": "ElevenLabs not available" } ] }
```

2) Audio only (content negotiation)
- Client sets `Accept: audio/mpeg`
- 200 OK
  - Headers: `Content-Type: audio/mpeg`, `X-Agent-Text: <url-escaped final text>`, `Cache-Control: no-store`
  - Body: raw MP3 bytes from ElevenLabs

Upstream TTS request (non‑stream)
- Endpoint: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128`
- Headers: `xi-api-key: <ELEVEN_LABS_API_KEY>`, `Content-Type: application/json`
- Body:
```json
{ "text": "Final answer", "model_id": "eleven_multilingual_v2" }
```
- Response: MP3 bytes. Default `output_format` is `mp3_44100_128` (44.1 kHz, 128 kbps). `optimize_streaming_latency` is for streaming endpoints and is not used in v1.

Config & privacy
- `ELEVEN_LABS_API_KEY` (secret), `ELEVEN_LABS_VOICE_ID` (optional, default: `56AoDkrOh6qfVPDXZ7Pt`)
- Generated audio is not persisted or logged; only final text is stored per normal logging rules.

## 9) Logging

GrandHotel Agent uses structured logging with different formats for development and production environments.

### Configuration

- **`APP_ENV`** — Environment mode (`development` / `production`)
  - **development**: Human-readable text format, `DEBUG` level, detailed traces for all operations
  - **production**: JSON format, `INFO` level, structured logs optimized for log aggregation systems (ELK, Loki, CloudWatch, Datadog)

- **`LOG_LEVEL`** — Optional override for log level (`DEBUG` / `INFO` / `WARNING` / `ERROR`)
  - Defaults to `DEBUG` in development, `INFO` in production
  - Can be set explicitly to override environment-based defaults

### Log Output

All logs are written to **stdout** for Docker compatibility. Use your container orchestration platform to collect and aggregate logs.

### Context Enrichment

Every log automatically includes:
- **sessionId** — User session UUID (from `ChatRequest.sessionId`)
- **traceId** — Optional client trace ID (from `ChatRequest.client.traceId`)
- **component** — Service layer (router, agent, fc, lang, redis, tool)
- **timestamp** — ISO8601 UTC timestamp
- **level** — Log severity level

### Example Log Output

**Development (text format):**
```
2025-11-18 14:32:01 | INFO     | grandhotel_agent.routers.agent | Request: POST /agent/chat | session=abc12345 trace=xyz78901
2025-11-18 14:32:02 | INFO     | grandhotel_agent.services.agent_service | Function calling: tool invoked | session=abc12345 trace=xyz78901
2025-11-18 14:32:02 | DEBUG    | grandhotel_agent.tools.rooms | Backend API call: rooms_list | session=abc12345
```

**Production (JSON format):**
```json
{
  "timestamp": "2025-11-18T14:32:01.123Z",
  "level": "INFO",
  "service": "grandhotel-agent",
  "component": "router",
  "message": "Request: POST /agent/chat",
  "sessionId": "abc12345-uuid-v4",
  "traceId": "xyz78901",
  "endpoint": "/agent/chat",
  "voice_mode": false
}
```

### Privacy & Security

- **User messages are NEVER logged** in production (GDPR/privacy compliance)
- Only metadata is logged: sessionId, traceId, language codes, tool names, durations, error types
- Function calling arguments logged only in development mode
- Sensitive backend responses are not included in logs

### Log Levels by Component

| Component | DEBUG | INFO | WARNING | ERROR |
|-----------|-------|------|---------|-------|
| **router** | Request details | Request start/success | — | Agent failures, validation errors |
| **agent (FC)** | Tool arguments (dev only) | Tool invocations | — | Tool execution failures, model errors |
| **lang** | Detected language codes | — | Invalid format, fallbacks | API errors |
| **redis** | — | — | Connection failures (non-blocking) | Critical session errors |
| **tool** | Backend calls, response counts | — | — | HTTP errors, timeouts |

### Switching Environments

**Local development:**
```bash
APP_ENV=development docker-compose up
```

**Production deployment:**
```bash
APP_ENV=production LOG_LEVEL=INFO docker-compose up
```

**Debugging in production** (temporary):
```bash
APP_ENV=production LOG_LEVEL=DEBUG docker-compose up
```
