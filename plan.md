# GrandHotel Agent — Plan wdrożenia (LLM‑only lang + pre‑flight)

## Cel
- Zapewnić, że agent zawsze odpowiada w języku użytkownika, bez statycznych heurystyk po stronie kodu.
- Zmniejszyć latency i koszt: wykrywać język lekkim modelem (pre‑flight), a główną odpowiedź generować pełnym modelem z Function Calling.
- Uporządkować prompt: na wejściu wyraźny sygnał „Klient pisze (Wykryj język w jakim napisał): …”, krótka FINAL CHECKS.

## Zasady (kontrakt)
- Zero statycznych detekcji/korekt języka w kodzie (brak heurystyk, brak regexów, brak translacji po stronie backendu).
- Detekcja języka wyłącznie przez LLM.
- Nie ujawniamy toku rozumowania, wewnętrznych kroków ani nazw narzędzi w odpowiedzi do użytkownika.

## Przepływ (wysoki poziom)
1) Pre‑flight: gemini‑2.5‑flash‑lite — wykryj język użytkownika (BCP‑47) na podstawie jego wiadomości.
2) Główne wywołanie: gemini‑2.5‑flash + Function Calling (tools), z poprawionym promtem.
3) Odpowiedź: tekst w języku użytkownika; pole `language` = wynik z pre‑flight (BCP‑47).
4) (Przyszłość) TTS: jeśli `voiceMode=true`, wybór `voice_id` po mapowaniu BCP‑47 → głos i wywołanie ElevenLabs (mp3_44100_128).

## Zmiany w promcie (grandhotel_agent/prompt.txt)
- Dodaj na wejściu (jako część treści użytkownika, by ustawić kontekst):
  - „Klient pisze (Wykryj język w jakim napisał): {USER_MESSAGE}”.
- Dodaj krótką sekcję pre‑flight (wewnętrzna, nieujawniana):
  - LANG = wykryty język użytkownika (BCP‑47).
  - INTENCJA = jedno zdanie („o co pyta klient”).
  - Twarda zasada: finalna odpowiedź MUSI być dokładnie w LANG; bez mieszania języków. Jeśli szkic nie w LANG, przetłumacz wewnętrznie i dopiero wyślij.
- Krótkie FINAL CHECKS (minimalne, niskie latency; wewnętrzne):
  - Czy odpowiedź jest w 100% w LANG?
  - Czy nie ujawniasz procesu/narzędzi?
  - Czy wszystkie konkrety są oparte na danych (bez zmyślania)?
  - Czy dopytujesz tylko, jeśli brakuje danych do kolejnego kroku (daty, goście, preferencje/budżet)?
  - Czy kończysz jednym jasnym CTA?

## Zmiany w serwisie agenta (grandhotel_agent/services/agent_service.py)
- Przekazać instrukcje jako `system_instruction` (zgodnie z SDK Google GenAI) — bez doklejania promptu do roli `user`.
- W `contents` przekazywać tylko wiadomość użytkownika (poprzedzoną frazą „Klient pisze (Wykryj język w jakim napisał): …”).
- Nie wykonywać żadnych językowych heurystyk ani post‑translacji po stronie backendu.
- Pętla Function Calling pozostaje bez zmian merytorycznych (wykrycie `function_call` → wykonanie → `function_response` → finalny tekst).

## Zmiany w routerze API (grandhotel_agent/routers/agent.py)
- Dodać pre‑flight wywołanie LLM (gemini‑2.5‑flash‑lite) do wykrycia języka wiadomości użytkownika:
  - System: „You are a strict language detector.”
  - User: „Return only the BCP‑47 language code of this text: <wiadomość>”
  - Parametry: `temperature=0`, bez narzędzi, oczekiwany output np. `pl-PL`, `en-US`.
- Ustawić `ChatResponse.language` na wynik pre‑flight.
- Nie wykonywać żadnych heurystyk ani fallbacków regexowych; w razie niepoprawnego wyniku — zwrócić bezpieczny default (np. `en-US`) i dodać ostrzeżenie w logu (nie w odpowiedzi do użytkownika).


## Obsługa błędów i krawędzie
- Pre‑flight zwrócił niepoprawny kod: zaloguj, ustaw bezpieczny default (`en-US`), kontynuuj; nie wyświetlaj błędu użytkownikowi.
- Treści mieszane językowo: detektor ma zwrócić dominujący język; prompt główny wymusza finalny język LANG.
- Brak narzędzia/timeout narzędzia: jasno poinformuj użytkownika i zaproponuj kolejny krok (np. podanie dat), bez halucynacji.

## Walidacja (manualna, szybka)
- EN input → EN reply, `language=en-US`.
- PL input → PL reply, `language=pl-PL`.
- Brak dublowania nazw narzędzi/procesu w odpowiedzi.
- FINAL CHECKS spełnione (krótka lista, niskie latency).

## Kryteria akceptacji
- Brak statycznych detektorów języka w repo.
- `language` w odpowiedzi ustawiane przez LLM (pre‑flight, lite model).
- Główna odpowiedź zawsze w języku użytkownika.
- Prompt zawiera wyraźne: „Klient pisze (Wykryj język w jakim napisał): …” oraz krótkie FINAL CHECKS.

## Rollout
- Etap 1: wprowadzić zmiany w prompt.txt, agent_service.py (system_instruction), routers/agent.py (pre‑flight lang LLM), bez TTS.
- Etap 2 (opcjonalnie): dodać mapowanie BCP‑47 → `voice_id`, endpoint TTS z ElevenLabs, feature flag `voiceMode`.

