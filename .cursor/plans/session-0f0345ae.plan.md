<!-- 0f0345ae-21dc-4545-8249-ce84e5f08604 62208b47-958f-4e24-b576-32317b875918 -->
# Plan: inteligentna pamięć rozmowy w oparciu o Redis

## 1) Nagłówek do SENSEI

Siemanko SENSEI, mam dla Ciebie task związany z dołożeniem prawdziwej pamięci konwersacji do GrandHotel Agenta. Obecnie mamy tylko techniczne sesje w Redis (TTL, `touch`), ale model zawsze dostaje pojedynczą wiadomość – celem jest, żeby przy każdym kolejnym wywołaniu widział całą (przyciętą) historię rozmowy w ramach `sessionId`, nie przepalał osobnego modelu do detekcji języka, jeśli język jest już znany z sesji, oraz miał w system prompt jasno opisane, jak traktować historię rozmowy.

## 2) Cel

- **Biznesowo**: użytkownik rozmawia z jednym „Concierge”, który pamięta wcześniejsze pytania i odpowiedzi w obrębie `sessionId`.
- **Technicznie**: przechowywanie historii Q/A w Redis w strukturze JSON oraz przekazywanie jej do Gemini jako poprzednich `user/model` message’ów.
- **Optymalizacja kosztu/latencji**: detekcja języka `GEMINI_MODEL_LANG` (`flash-lite`) wykonywana tylko dla nowej sesji (brak historii lub brak zapisanego języka); dla kolejnych wiadomości używamy `language` z Redis.
- **Guidance w prompt**: system prompt (`prompt.txt`) wyjaśnia modelowi, że oprócz bieżącej wiadomości może dostawać historię rozmowy i jak ma ją wykorzystywać (jeśli jest, traktuj ją jako kontekst; jeśli brak, traktuj wiadomość jak pierwszą).
- **Bezpieczeństwo i stabilność**: degradacja łagodna – jeśli Redis padnie, agent dalej odpowiada, ale bez pamięci i bez reuse języka.
- **Skalowalność**: prosty limit długości historii (N ostatnich wiadomości) konfigurowany z ENV, bez przedwczesnego over-engineeringu (podsumowania itp. można dołożyć później).

## 3) Pliki do pełnej analizy PRZED startem

- `grandhotel_agent/routers/agent.py` – główny endpoint `/agent/chat`, dziś: walidacja requestu, wyciągnięcie JWT, `touch` sesji w Redis, detekcja języka, wywołanie `AgentService.chat`.
- `grandhotel_agent/services/agent_service.py` – logika Gemini FC loop, tu będziemy dokładali wsparcie dla historii (parametr `history` i budowa listy `contents`).
- `grandhotel_agent/services/redis_store.py` – obecny store sesji w Redis (`get/set/touch`, TTL, key `sessions:{sessionId}`), baza pod przechowywanie historii i języka.
- `grandhotel_agent/models/requests.py` – model `ChatRequest` z `sessionId`, upewnienie się, że semantyka sessionId jest spójna (UUID v4 z frontu).
- `grandhotel_agent/models/responses.py` – `ChatResponse` (dla kontekstu, czy trzeba coś dopisywać – raczej nie).
- `grandhotel_agent/config.py` – miejsce na konfigurację limitu historii (np. `SESSION_MAX_MESSAGES`).
- `grandhotel_agent/prompt.txt` – system prompt concierge; trzeba dopisać krótki blok o historii rozmowy, który model ma respektować.

## 4) Zakres zmian – po plikach / modułach

### `config.py` (XS)

- Dodać nowy parametr konfiguracyjny: np. `SESSION_MAX_MESSAGES = int(os.getenv("SESSION_MAX_MESSAGES", "20"))` (lub podobny), opisany w komentarzu jako limit łącznej liczby wiadomości w historii (czyli lista `messages` w Redis).
- (Opcjonalnie) dodać drugi parametr znakowy/„tokenowy”, jeśli uznamy, że warto (np. `SESSION_MAX_CHARS`), ale na start wystarczy liczba wiadomości.

### `services/redis_store.py` (S)

- Ustalić standardową strukturę danych sesji w Redis, np.:
- `{"createdAt": <ISO8601>, "messages": [ {"role": "user"|"assistant", "content": "...", "ts": <ISO8601> }, ... ], "language": "pl-PL"}`.
- Zmodyfikować `touch` tak, aby przy tworzeniu nowej sesji od razu inicjalizował strukturę zgodną z powyższym (np. `createdAt` + pusta lista `messages`, bez pola `language` na starcie), zamiast `{ "created": True }`.
- Dodać prostą funkcję pomocniczą (lub przynajmniej jasno udokumentować użycie istniejących):
- odczyt sesji: `session = await store.get(session_id)` → zawsze zwracamy `dict` lub `None`, przy czym brak `messages` traktujemy jako pustą listę;
- zapis sesji: `await store.set(session_id, session_dict)` – TTL zarządzany jak obecnie.
- Nie zmieniać ogólnej semantyki TTL i kluczy – nadal `sessions:{sessionId}`, TTL z `SESSION_TTL_MIN`.

### `services/agent_service.py` (M-)

- Rozszerzyć sygnaturę `AgentService.chat` o opcjonalny parametr historii, np.:
- `async def chat(self, user_message: str, jwt: str | None = None, language_code: str | None = None, history: list[dict] | None = None) -> tuple[str, list[ToolTrace]]`.
- Zmienić budowę listy `contents` tak, aby:
- startowo była pusta (`contents: list[types.Content] = []`),
- jeśli `history` jest przekazane, przeiterować po niej i dla każdego elementu w standardowym formacie:
- `{"role": "user", "content": "..."}` → `types.Content(role="user", parts=[types.Part(text=content)])`,
- `{"role": "assistant", "content": "..."}` → `types.Content(role="model", parts=[types.Part(text=content)])`;
- na końcu **zawsze** dodać bieżącą wiadomość użytkownika jako ostatni element `contents` (`role="user"`).
- Reszta FC loop (wywołanie modelu, parsowanie `function_call`, ponowne wywołanie z dołączoną odpowiedzią narzędzia) pozostaje bez zmian – korzysta z tej samej listy `contents`, która teraz zawiera całą historię.
- Dodać prostą walidację historii (np. ignorować wpisy bez `content` lub z nieoczekiwanym `role`) tak, aby stare sesje z minimalnymi danymi nie psuły flow.

### `routers/agent.py` – endpoint `/agent/chat` (M)

- Zastąpić obecny blok „Touch Redis session” czymś w rodzaju:
- spróbować pobrać `store = await get_session_store()`;
- spróbować `session = await store.get(request.sessionId)` (w `try/except`, przy błędzie → `store = None`, `session = None`, kontynuujemy bez sesji);
- z `session` wyciągnąć `history = session.get("messages", [])` jeśli to lista, w przeciwnym wypadku pustą listę.
- Logika języka:
- jeśli `session` zawiera pole `"language"` (i jest ono niepuste), używać go jako `language_code` **bez** wywoływania `detect_language_bcp47`;
- jeśli `session` nie istnieje, nie ma `language` albo historia jest pusta (`history == []`), wywołać `detect_language_bcp47(request.message)` jak dotąd;
- po udanej detekcji zapisać `language` w sesji (patrz niżej).
- Przy wywołaniu agenta przekazać historię i ustalone `language_code`:
- `reply, tool_traces = await agent.chat(user_message, jwt, language_code, history=history)`.
- Po otrzymaniu odpowiedzi zaktualizować sesję (jeśli `store` jest dostępne):
- zbudować nową listę `messages = history + [ {"role": "user", "content": user_message, "ts": <now_iso>}, {"role": "assistant", "content": reply, "ts": <now_iso>} ]`;
- przyciąć listę do maksymalnej długości: np. `messages = messages[-SESSION_MAX_MESSAGES:]`;
- zaktualizować `session` (tworząc pusty dict, jeśli `session is None`) i ustawić `session["messages"] = messages` oraz **zawsze** `session["language"] = language_code` (o ile nie jest `None`);
- zapisać `await store.set(request.sessionId, session)`;
- cały blok owinąć w `try/except` – w razie problemów z Redisem logować i NIE przerywać obsługi requestu.
- Zachować dotychczasowy `ChatResponse` bez zmian – pamięć konwersacji i język działają w tle, kontrakt API się nie zmienia.

### `prompt.txt` – system prompt (XS)

- Na końcu promptu dopisać krótki blok o historii rozmowy, np. w stylu:
- `Historia rozmowy`
- `- Możesz otrzymywać historię poprzednich wiadomości w tej samej sesji (user/assistant).`
- `- Jeśli historia jest pusta, traktuj bieżące pytanie jak pierwsze w nowej rozmowie.`
- `- Jeśli historia jest niepusta, wykorzystaj ją jako kontekst odpowiedzi, nie powtarzaj jednak mechanicznie całej treści — odnoś się do niej naturalnie.`
- Ten blok nie zmienia technicznej reprezentacji historii (dalej przekazujemy ją jako listę `user/model` message’ów), ale eksplicytnie komunikuje modelowi, jak ma się zachować przy obecności/nieobecności historii.

## 5) Szczegóły implementacyjne

- **Format historii w Redis**:
- Ustalamy prosty, czytelny format: `messages: list[{"role": "user"|"assistant", "content": str, "ts": str}]` oraz pole `language: str` przechowujące ostatnio używany kod BCP-47 w sesji.
- Stare sesje (tylko `{"created": True}` albo brak klucza) obsługujemy defensywnie: jeśli `session.get("messages")` nie jest listą → traktujemy, jakby historii nie było; jeśli `language` brak, będzie dopiero zapisany przy pierwszym poprawnym wywołaniu detekcji.
- **Integracja z Gemini**:
- Korzystamy z natywnego sposobu reprezentacji historii: lista `Content` z rolą `user` dla wejść użytkownika i `model` dla odpowiedzi asystenta.
- Nie budujemy sztucznego tekstu typu „Client asked / You answered…” – historia jest czytelna dla modelu dzięki poprawnym rolom; jeśli kiedyś będzie potrzeba, można to łatwo dorzucić jako dodatkową metainstrukcję.
- Nowy blok w `prompt.txt` tylko opisuje semantykę historii (że może być pusta lub niepusta) i oczekiwane zachowanie modelu.
- **Limitowanie historii**:
- Pierwsza wersja: prosty limit liczby wiadomości (`SESSION_MAX_MESSAGES`), przycinany od początku (zostawiamy najnowsze).
- To daje stabilną liczbę message’ów w promptcie bez liczenia tokenów; jeśli w praktyce pojawią się problemy z długością kontekstu, można później dołożyć funkcję podsumowującą starą część historii.
- **Reuse języka i fallback**:
- Jeśli w sesji mamy `language`, **nie** wywołujemy `detect_language_bcp47` – dzięki temu unikamy dodatkowego requestu do modelu i przyspieszamy odpowiedź.
- Jeżeli `language` jest `None` / brak, uruchamiamy detekcję dokładnie raz na początku (przy pierwszej wiadomości) i zapisujemy wynik w sesji; przy kolejnych requestach używamy go bez ponownej detekcji.
- Każde użycie store (`get_session_store`, `get`, `set`) w routerze opakowujemy w `try/except` i w razie błędu tylko logujemy, nie przerywając flow: w takim przypadku `history` jest po prostu pusta, a język wykrywany każdorazowo standardową ścieżką.

## 6) Testy i walidacja

- **Testy jednostkowe / integracyjne (jeśli dodamy testy)**:
- Sprawdzić, że `SessionStore` poprawnie zapisuje i odczytuje strukturę `messages` oraz `language` oraz że TTL nadal działa (np. przez inspekcję `ttl` klucza w Redis w testowym środowisku).
- Test dla `AgentService.chat` z prostą, sztuczną `history` (np. jedna poprzednia para Q/A) – upewnić się, że metoda poprawnie buduje listę `contents` (można to sprawdzić przez stub/mock klienta Gemini).
- **Testy manualne endpointu `/agent/chat`**:
- Scenariusz 1: nowa sesja (`sessionId` wcześniej nieużywany) → pierwsze pytanie, odpowiedź, sprawdzenie w Redis, że powstał dokument z `messages` zawierającym 2 wpisy (user + assistant) oraz że pole `language` jest ustawione na wykryty kod.
- Scenariusz 2: to samo `sessionId`, kolejne pytanie nawiązujące do poprzedniego kontekstu → zweryfikować, że model realnie korzysta z pamięci (odnosi się do wcześniejszej części rozmowy) i że w Redis lista `messages` rośnie, przy czym liczba nie przekracza `SESSION_MAX_MESSAGES`; dodatkowo potwierdzić w logach, że drugi i kolejne requesty **nie** wywołują `detect_language_bcp47`.
- Scenariusz 3: wymuszone problemy z Redis (np. zły URL w ENV w środowisku lokalnym) → endpoint dalej odpowiada, ale bez historii i bez reuse języka; logi zawierają komunikat błędu Redis.
- Scenariusz 4: sanity-check system prompt – czy nowy blok o historii poprawnie trafia do konfiguracji modelu (sprawdzić, że `self.system_prompt` zawiera tę sekcję i że jest doklejana do `system_instruction`).

## 7) Ryzyka i punkty uwagi

- **Rozmiar promptu / koszt** (Średni): jeśli użytkownik długo rozmawia w jednej sesji, historia rośnie – ograniczamy to przez `SESSION_MAX_MESSAGES`, ale warto dobrać rozsądną wartość (np. 20–40 wiadomości) i ewentualnie zweryfikować w praktyce.
- **Spójność struktury sesji** (Średni): istniejące sesje mogą mieć inną strukturę (np. tylko `created`). Dlatego kod musi być defensywny (treat-as-empty, gdy `messages` brak lub ma zły typ; brak `language` → jedna detekcja i zapis).
- **Zachowanie przy równoległych requestach do tej samej sesji** (Niski): teoretycznie dwa równoległe żądania mogą nadpisać sobie nawzajem historię; przy typowym użyciu (1 klient → 1 request naraz) to akceptowalne. Jeśli w przyszłości będzie problem, można dołożyć prostą blokadę/`WATCH/MULTI` w Redis.
- **Zmiany w API Gemini** (Niski): trzeba upewnić się, że używane role (`user`/`model`) i struktura `Content` są zgodne z aktualną wersją SDK; w razie zmian – dostosować mapowanie.
- **Spójność promptu** (Niski): nowy blok o historii powinien stylistycznie pasować do reszty promptu; warto zachować ten sam ton i strukturę (krótkie, konkretne bullet pointy).

## 8) Pytania dla użytkownika / ewentualnie do SENSEI-PLANNER

- Czy limit historii na start ustawiamy na konkretną wartość (np. 20 wiadomości), czy zostawiamy to w pełni konfigurowalne i na produkcji dobierzesz samemu przez ENV?
- Czy chcesz w przyszłości rozszerzyć to o automatyczne podsumowywanie starszej części historii (np. po przekroczeniu progu), czy na razie trzymamy się prostego przycinania listy?
- Jeśli podczas implementacji pojawi się niejasność (np. co do formatu sesji, strategii limitowania, dodatkowych pól czy dokładnej treści bloku o historii w `prompt.txt`), SENSEI powinien spisać szczegółowe pytania i wrócić do SENSEI-PLANNER przed wprowadzeniem własnych założeń.

### To-dos

- [ ] Dodać do `config.py` konfigurację limitu historii sesji (np. `SESSION_MAX_MESSAGES`) i ewentualnie prosty limit znakowy.
- [ ] Ustalić i zaimplementować docelową strukturę danych sesji w Redis (pola `messages` + `language`, poprawiona inicjalizacja w `touch`).
- [ ] Rozszerzyć `AgentService.chat` o opcjonalny parametr historii oraz budowanie listy `contents` z użyciem poprzednich wiadomości.
- [ ] Zmienić endpoint `/agent/chat` tak, aby ładował sesję z Redis, korzystał z pola `language` do pomijania detekcji, przekazywał historię do `AgentService.chat` i po odpowiedzi zapisywał zaktualizowaną historię.
- [ ] Dopisać do `prompt.txt` krótki blok o historii rozmowy (jeśli historia jest pusta – traktuj wiadomość jak pierwszą; jeśli nie – używaj historii jako kontekstu).
- [ ] Przygotować podstawowe testy (jednostkowe/integracyjne lub manualne) weryfikujące zapis/odczyt historii i `language` w Redis, poprawne wykorzystanie historii przez model oraz obecność nowego bloku w system prompt.