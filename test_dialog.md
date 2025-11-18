# Testy Postman - GrandHotel Agent Chat API

## Konfiguracja Postman

**Endpoint:** `POST http://localhost:8000/agent/chat`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer fake-jwt-token
```

---

## Scenariusz 1: Nowa sesja - pierwsze pytanie (Polski)

**Cel:** Testowanie nowej sesji, detekcji jzyka (pl-PL), utworzenia sesji w Redis

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-001",
  "message": "Witam! Szukam pokoju na weekend dla 2 osób.",
  "voiceMode": false
}
```

**Oczekiwany wynik:**
- `language: "pl-PL"`
- Odpowiedz po polsku
- Redis: utworzona sesja z `messages: [2 wpisy]`, `language: "pl-PL"`

---

## Scenariusz 2: Kontynuacja rozmowy (ten sam sessionId)

**Cel:** Testowanie pamici rozmowy, reuse jzyka (BEZ detekcji), kontekstu historii

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-001",
  "message": "A jakie s ceny tych pokoi?",
  "voiceMode": false
}
```

**Oczekiwany wynik:**
- `language: "pl-PL"` (z sesji, NIE z detekcji)
- Odpowiedz nawizujca do poprzedniego kontekstu
- Redis: `messages` ro[nie (teraz 4 wpisy)
- **W logach NIE powinno by:** `[Lang] ...` (brak detekcji jzyka)

---

## Scenariusz 3: Nowa sesja - English

**Cel:** Testowanie detekcji jzyka angielskiego

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-en-002",
  "message": "Hello! I'm looking for a room for 3 nights.",
  "voiceMode": false
}
```

**Oczekiwany wynik:**
- `language: "en-US"` (lub `en-GB`)
- Odpowiedz po angielsku
- Redis: nowa sesja z `language: "en-US"`

---

## Scenariusz 4: Pytanie wymagajce Function Calling (rooms_list)

**Cel:** Testowanie wywoBania narzdzia rooms_list, toolTrace w odpowiedzi

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-fc-003",
  "message": "Poka| mi wszystkie dostpne pokoje w hotelu",
  "voiceMode": false
}
```

**Oczekiwany wynik:**
- `toolTrace: [{"name": "rooms_list", "status": "OK", "durationMs": ...}]`
- Odpowiedz zawiera list pokoi z backendu
- **W logach:** `[FC] Tool called: rooms_list`

---

## Scenariusz 5: DBuga konwersacja (test limitu SESSION_MAX_MESSAGES=30)

**Cel:** Testowanie trimowania historii po przekroczeniu 30 wiadomo[ci

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-long-004",
  "message": "Kolejna wiadomo[ w dBugiej rozmowie...",
  "voiceMode": false
}
```

**Instrukcja:**
1. Wy[lij 16+ requestów z tym samym sessionId (ka|dy dodaje 2 wpisy: user + assistant)
2. Po 16. reque[cie: `messages.length = 32` ’ trim do 30
3. Sprawdz w Redis (`redis-cli`): `GET sessions:test-session-long-004`
4. Zweryfikuj |e `messages` ma max 30 elementów

**Komenda Redis CLI:**
```bash
docker exec -it grandhotel-redis redis-cli
GET sessions:test-session-long-004
```

---

## Scenariusz 6: Audio input (placeholder - TODO)

**Cel:** Testowanie obsBugi audio (obecnie zwraca placeholder)

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-audio-005",
  "message": null,
  "audio": {
    "data": "fake_base64_audio_data",
    "mimeType": "audio/webm",
    "durationMs": 3500
  },
  "voiceMode": true
}
```

**Oczekiwany wynik:**
- `user_message: "[Audio input - transcription TODO]"`
- Odpowiedz tekstowa (TTS TODO)

---

## Scenariusz 7: Graceful degradation - Redis down

**Cel:** Testowanie dziaBania bez Redis (agent dalej odpowiada, ale bez pamici)

**Instrukcja:**
1. Zatrzymaj Redis: `docker stop grandhotel-redis`
2. Wy[lij request:

**Body (raw JSON):**
```json
{
  "sessionId": "test-session-no-redis-006",
  "message": "Test bez Redis",
  "voiceMode": false
}
```

**Oczekiwany wynik:**
- Status 200 (NIE 500)
- Odpowiedz generowana (bez historii)
- **W logach:** `[Redis] Error loading session: ...`
- Detekcja jzyka wykonywana (brak reuse)

3. Uruchom Redis: `docker start grandhotel-redis`

---

## Weryfikacja sesji w Redis

**Komenda:**
```bash
# PodBcz si do Redis CLI
docker exec -it grandhotel-redis redis-cli

# Sprawdz klucze sesji
KEYS sessions:*

# Pobierz konkretn sesj
GET sessions:test-session-001

# Sprawdz TTL (60 min = 3600s)
TTL sessions:test-session-001

# Wyczy[ wszystkie sesje (ostro|nie!)
FLUSHDB
```

**PrzykBadowa struktura sesji w Redis:**
```json
{
  "createdAt": "2025-11-18T14:30:00.123456+00:00",
  "messages": [
    {
      "role": "user",
      "content": "Witam! Szukam pokoju na weekend dla 2 osób.",
      "ts": "2025-11-18T14:30:00.123456+00:00"
    },
    {
      "role": "assistant",
      "content": "Witam! Z przyjemno[ci pomog Ci znalez idealny pokój...",
      "ts": "2025-11-18T14:30:02.456789+00:00"
    }
  ],
  "language": "pl-PL"
}
```

---

## Tips dla testowania w Postmanie

1. **Zmienne [rodowiskowe:**
   - `base_url: http://localhost:8000`
   - `session_id: {{$guid}}` (auto-generate UUID)

2. **Collection Runner:**
   - Uruchom scenariusze 1-4 sekwencyjnie
   - Sprawdz czy `language` jest konsekwentnie reused

3. **Tests tab (JavaScript validation):**
```javascript
pm.test("Status 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has language", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.language).to.exist;
});

pm.test("Reply not empty", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.reply).to.not.be.empty;
});
```

---

## Checklist walidacji (wszystkie scenariusze)

- [ ] Nowa sesja tworzy wpis w Redis z `createdAt`, `messages`, `language`
- [ ] Kontynuacja rozmowy Baduje histori z Redis
- [ ] Detekcja jzyka wykonywana tylko raz (przy nowej sesji)
- [ ] Kolejne requesty reu|ywaj `language` z sesji
- [ ] Model otrzymuje caB histori (widoczne w odpowiedziach kontekstowych)
- [ ] Historia jest trimowana do max 30 wiadomo[ci
- [ ] Function Calling dziaBa i toolTrace jest zwracany
- [ ] Redis failure NIE blokuje odpowiedzi (graceful degradation)
- [ ] TTL sesji jest od[wie|any przy ka|dym request (sliding window)
