# GrandHotel Agent v1 — Ujednolicone API (bez streamu)

## 1) Opis
- Jeden endpoint do obsługi tur: `POST /agent/chat`; zdrowie: `GET /agent/health`.
- Model: `gemini-2.5-flash` z thinking + Function Calling (FC).
- Opcjonalny TTS (ElevenLabs) przy `voiceMode=true`.
- Brak WebSocket/SSE w v1.

## 2) Autoryzacja i sesje
- `/agent/chat` wymaga `Authorization: Bearer <JWT>`; ufamy `sub/role/given_name`; JWT przekazujemy do backendu.
- Front generuje `sessionId` (UUID v4) przed pierwszym wywołaniem i dołącza go do każdego żądania.
- Agent automatycznie tworzy sesję w Redis przy pierwszym użyciu `sessionId`; TTL przesuwne = 60 min (odświeżane przy każdej turze). Nowa rozmowa = nowy `sessionId`.
- Opcjonalnie: jeśli w JWT brak imienia, Agent 1× woła `/api/v1/me` i cache’uje.

## 3) Limit zapytań
- 30 żądań/min na `sessionId`. Po przekroczeniu: 429 z `{ code: "RATE_LIMITED", retryAfter: <sekundy> }`.

## 4) Endpointy
### 4.1 `GET /agent/health` (public)
- 200 OK
```json
{ "status": "ok", "version": "1.0.0" }
```

### 4.2 `POST /agent/chat`
Nagłówki
- `Authorization: Bearer <JWT>`
- `Content-Type: application/json`
- `Accept: application/json` (domyślnie) LUB `audio/mpeg` (gdy `voiceMode=true` i chcemy surowe audio)

Body (wymagane: `message` lub `audio`; oba dozwolone — `message` to dodatkowy prompt do audio)
```json
{
  "sessionId": "uuid-v4",
  "message": "opcjonalny tekst",
  "audio": { "mimeType": "audio/wav|audio/mp3|audio/aiff|audio/aac|audio/ogg|audio/flac", "data": "<base64>" },
  "voiceMode": false,
  "client": { "traceId": "opcjonalnie <=64" }
}
```
Uwagi
- Maksymalny rozmiar żądania inline (tekst+audio+system) ≤ 20 MB (limit REST Gemini). Większe audio planujemy obsłużyć przez Files API.
- Przetwarzanie: Agent buduje prompt (system + krótki skrót historii + imię? + bieżące wejście), włącza thinking, dołącza FC `functionDeclarations`, woła `gemini-2.5-flash`.
- Jeśli model zwróci `functionCall{name,args}`: walidacja (Zod), wywołanie Backend z JWT, `functionResponse` do modelu, potem finalny tekst.
- Gdy `voiceMode=true`: generujemy MP3 (ElevenLabs `mp3_44100_128`) i dołączamy do odpowiedzi.

200 OK (JSON)
```json
{
  "sessionId": "uuid-v4",
  "language": "pl-PL",
  "reply": "Finalna odpowiedź",
  "audio": { "mimeType": "audio/mpeg", "data": "<base64>" },
  "toolTrace": [ { "name": "rooms_filter", "status": "OK", "durationMs": 142 } ]
}
```
- `audio` pomijamy przy `voiceMode=false`; `toolTrace` jest opcjonalny.

200 OK (audio w body)
- Jeżeli `Accept: audio/mpeg` ORAZ `voiceMode=true` → body = surowe MP3; nagłówek `X-Agent-Text: <url-escaped finalny tekst>`.

Błędy (wspólny format)
```json
{ "code": "STRING_CONST", "message": "Opis", "status": 400, "traceId": "opcjonalnie", "details": { "field": "kontekst" } }
```
- Przykłady: 400 BAD_REQUEST (błędny input/nieobsługiwany mime), 413 PAYLOAD_TOO_LARGE (>20MB inline), 401/403 auth, 422 reguły biznesowe, 429 RATE_LIMITED, 500 INTERNAL_ERROR, 502 BACKEND_5XX.

## 5) Function Calling — narzędzia → backend
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

## 6) Prywatność
- Do modelu wysyłamy tylko imię; bez maili/telefonów/ID.
- Nie przechowujemy surowego audio; transkrypt/skrót historii trzymamy w Redis tylko przez TTL sesji.

## 7) Przykłady
Tekst
```http
POST /agent/chat
Authorization: Bearer <JWT>
Content-Type: application/json
Accept: application/json

{"sessionId":"b1d6c0f0-4a1d-4e3c-9b23-6e7c1c8a2f01","message":"Pokój dla 3 osób 24–27.10","voiceMode":false}
```

Audio
```http
POST /agent/chat
Authorization: Bearer <JWT>
Content-Type: application/json
Accept: application/json

{"sessionId":"b1d6c0f0-4a1d-4e3c-9b23-6e7c1c8a2f01","audio":{"mimeType":"audio/mp3","data":"<base64>"},"voiceMode":true}
```

## 8) Tryb głosowy (TTS) — ElevenLabs
- Gdy `voiceMode=true`, Agent najpierw uzyskuje finalny tekst od Gemini, a następnie wywołuje ElevenLabs Text‑to‑Speech i zwraca audio w jednym z dwóch formatów.

1) JSON (domyślnie)
- 200 OK
```json
{
  "sessionId": "uuid-v4",
  "language": "pl-PL",
  "reply": "Finalna odpowiedź",
  "audio": { "mimeType": "audio/mpeg", "data": "<base64 MP3>" },
  "toolTrace": [ { "name": "rooms_filter", "status": "OK", "durationMs": 142 } ]
}
```
- Uwaga: `reply` zawsze obecne; gdy TTS się nie powiedzie — pomijamy `audio` i dodajemy ostrzeżenie:
```json
{ "warnings": [ { "code": "TTS_UNAVAILABLE", "message": "ElevenLabs niedostępne" } ] }
```

2) Tylko audio (negocjacja treści)
- Klient ustawia `Accept: audio/mpeg`
- 200 OK
  - Nagłówki: `Content-Type: audio/mpeg`, `X-Agent-Text: <url-escaped tekst>`, `Cache-Control: no-store`
  - Body: surowe bajty MP3 z ElevenLabs

Wywołanie TTS (bez streamu)
- Endpoint: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128`
- Nagłówki: `xi-api-key: <ELEVENLABS_API_KEY>`, `Content-Type: application/json`
- Body:
```json
{ "text": "Finalna odpowiedź", "model_id": "eleven_multilingual_v2" }
```
- Odpowiedź: bajty MP3. Domyślny `output_format` to `mp3_44100_128` (44.1 kHz, 128 kbps). `optimize_streaming_latency` dotyczy endpointów streamingowych i nie jest używany w v1.

Konfiguracja i prywatność
- `ELEVENLABS_API_KEY` (sekret), `VOICE_ID_DEFAULT` (opcjonalne mapowanie głosu per język)
- Wygenerowanego audio nie przechowujemy ani nie logujemy; w logach pozostaje wyłącznie finalny tekst wg standardowych zasad.
