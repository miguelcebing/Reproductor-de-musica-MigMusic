# Estrategia y reporte de pruebas (F11)

> Fuente de verdad de calidad: `AGEND.md` (`TEST-001..004`) y `docs/skills/SKILL6.md`.
> Actualizado: 2026-10-01 (OAuth, música local tras F5, Framer Motion, correcciones
> UX, y el reproductor: resiliencia ante reinicio del backend, UI optimista,
> rendimiento del hilo principal, auto-avance y limpieza de código).

## 1. Pirámide y herramientas (`TEST-001`)

| Nivel | Herramienta | Dónde |
|---|---|---|
| Unitarias backend | `pytest` + `pytest-cov`, `hypothesis` (`TEST-004`) | `backend/tests/unit` |
| Integración / contrato | `pytest` + `TestClient`, adaptador SQL con `pgserver` (PostgreSQL embebido) | `backend/tests/integration` |
| Unitarias frontend | `Vitest` (entorno node, sin DOM) | `frontend/src/**/*.test.ts` |
| E2E | `Playwright` (desktop Chrome + Pixel 7) | `frontend/e2e` |
| Accesibilidad | `@axe-core/playwright` sobre Playwright | `frontend/e2e/a11y.spec.ts` |
| Estáticos | `ruff` + `ruff format` + `mypy --strict`; `eslint` + `tsc -b` | CI |

## 2. Cómo ejecutar

```powershell
# Backend (desde backend/)
uv run ruff check . ; uv run ruff format --check . ; uv run mypy
uv run pytest --cov=src/migmusic --cov-report=term --cov-fail-under=80
uv run coverage report --include="*/migmusic/domain/*" --fail-under=95
# Auditoría de dependencias (sin vulnerabilidades conocidas)
uv run pip-audit --skip-editable

# Frontend (desde frontend/)
npm run lint ; npm run typecheck
npm run test -- --run        # Vitest
npm run build
npm run test:e2e             # Playwright; una vez: npx playwright install chromium
```

La suite E2E es hermética: no necesita `.env`, arranca Vite (5173) y Uvicorn (8000) sola,
fuerza `DATABASE_URL=""` (repositorio in-memory, nunca toca una base real) y resetea los
playlists vía API en cada test.

### Cómo comprobar rate limiting y cabeceras a mano

```powershell
# Cabeceras de seguridad en la API (backend local o vía el proxy):
curl -sI http://127.0.0.1:8000/api/health
#   X-Content-Type-Options: nosniff · X-Frame-Options: DENY · Referrer-Policy
#   Content-Security-Policy: default-src 'none'; frame-ancestors 'none'

# Rate limiting en un endpoint estricto (búsqueda/letras): 429 + Retry-After
1..25 | ForEach-Object { curl -s -o NUL -w "%{http_code} " -H "X-Device-Id: manual-test" `
    "http://127.0.0.1:8000/api/youtube/search?q=a" }
#   Los primeros N (RATE_LIMIT_EXPENSIVE_PER_MINUTE) responden 200; el resto 429.

# Cuerpo demasiado grande: 413
curl -s -o NUL -w "%{http_code}" -X POST http://127.0.0.1:8000/api/playlists `
    -H "Content-Type: application/json" -H "X-Device-Id: manual-test" `
    --data-binary ("{\"name\":\"" + ("x" * 70000) + "\"}")
```

La comprobación automática equivalente vive en `backend/tests/integration/test_security_middleware.py`.

## 3. Estado actual (2026-10-03)

| Métrica | Umbral (`TEST-002`) | Actual |
|---|---|---|
| Cobertura global backend | ≥ 80 % | **94.3 %** |
| Cobertura `domain/` | ≥ 95 % | **99 %** |
| Tests backend | — | **401** (unit + integración + property-based) |
| Tests frontend (Vitest) | — | **147** (15 archivos) |
| Tests E2E (Playwright) | — | **21** (12 specs: smoke, maestro ×2, drag & drop, persistencia local, axe ×3, diálogo Spotify, bordes del transporte, aislamiento por dispositivo, reload, auto-avance, inicio inmediato, letras ×2) |
| Violaciones axe (WCAG 2.1 A/AA) | 0 | **0** (light, dark y diálogo abierto) |
| Auditoría de dependencias | 0 vulnerabilidades | **0** (`pip-audit` + `npm audit --omit=dev`) |
| Jobs de CI (`TEST-003`) | bloquean | `backend`, `frontend`, `e2e`, `no-secrets` |

### Suites añadidas en esta rama (F12/F13/SEC-001)

| Área | Archivo | Qué cubre |
|---|---|---|
| Segundo plano | `frontend/src/services/mediaSession.test.ts` | Metadata + acciones play/pausa/seek, estado playing/paused, limpieza y ausencia de API |
| Segundo plano | `frontend/src/services/playbackResilience.test.ts` | Reanudación al volver a visible, silencio estando oculto, `stop()` |
| Reproducción inmediata | `frontend/src/services/PlaybackController.test.ts` (+5) | `select` optimista con `loading`, parada del audio anterior, cancelación de la petición previa, respuesta `aborted` muda |
| Reproducción inmediata | `frontend/src/players/YouTubePlayer.test.ts` (actualizado) | Reutiliza el mismo iframe (`loadVideoById`) y `destroy()` no recrea el player |
| Reproducción inmediata | `frontend/e2e/instant-play.spec.ts` | Mide clic→título y clic→audio; ráfaga de clics → solo suena la última |
| Letras | `backend/tests/unit/test_application/test_lyrics_service.py` | Estrategia fuente-propia → LRCLIB, fallo = miss, caché de misses |
| Letras | `backend/tests/unit/test_infrastructure/test_lrclib_client.py` | Plain/LRC, 404 = miss, 5xx y timeout = error de upstream |
| Letras | `backend/tests/integration/test_lyrics_api.py` | 200 con texto, 204 sin letras, 422 con título vacío/enorme |
| Letras | `frontend/src/services/LyricsController.test.ts` | Resultado, 204→vacío, caché por canción, error cacheado |
| Letras | `frontend/e2e/lyrics.spec.ts` | Panel con texto y con estado vacío (respuesta interceptada) |
| Seguridad | `backend/tests/integration/test_security_middleware.py` | 429 por presupuesto + `Retry-After`, aislamiento por device-id, health exento, `RATE_LIMIT_ENABLED=false`, 413 y cabeceras |
| Seguridad | `frontend/src/services/localTracks.test.ts` | MP3/WAV por extensión y MIME, MIME vacío, formatos no admitidos, límite de tamaño |

## 4. Reporte: criterio → evidencia → estado

Equivale a la tabla que exige `SKILL6.md` §"Reporte final".

| Criterio de aceptación (`AGEND.md`) | Evidencia | Estado |
|---|---|---|
| Lista doblemente enlazada con enlaces reales, head/tail/current/size | `doubly_linked_list.py` + 40+ tests unitarios y `test_doubly_linked_list_properties.py` (hypothesis) | ✅ |
| Operaciones mínimas y casos borde probadas | `backend/tests/unit/test_structures/` + frontend `DoublyLinkedList` | ✅ |
| La playlist activa usa la lista y el agente puede explicar cómo | `PlaylistService` sobre `DoublyLinkedList` (ADR-001) | ✅ |
| Play/Pause/Next/Previous/Seek/Volume/Mute con audio real | E2E `master-flow` (desktop + Pixel 7) con WAV real; unit tests de controladores | ✅ |
| Skip ±N exacto sin salirse de límites (`PLAYER-001/002`) | E2E + tests de `PlaybackService.skip` (clamp 0…duración) | ✅ |
| Agregar (inicio/final/posición), eliminar y seleccionar desde la UI | E2E: 3 pistas, insert en índice 1, quitar la pista activa | ✅ |
| Música local: File Picker, play/pause/seek/cambio/eliminar | E2E con `setInputFiles` + `LocalAudioPlayer` tests | ✅ |
| Spotify: OAuth, refresh, Web Playback SDK, errores | Código + dobles en unit tests (`SpotifyPlayer`, `AuthController`); cuenta Premium pendiente | ⚠️ |
| Fuentes separadas y polimórficas | `AudioSource` (F5), inyección en `PlaybackController` | ✅ |
| Capas respetadas sin lógica en rutas/componentes | ADR-002; routers solo delegan a servicios | ✅ |
| POO: ABC, polimorfismo, DI, SOLID | `PlaylistRepository` (in-memory/SQL), `AudioSource`, `TokenStore` | ✅ |
| Backend 100 % Python, código en inglés | `backend/` (ruff + mypy strict en CI) | ✅ |
| Sin secretos en repo ni frontend; `.env.example` | Job CI `no-secrets` | ✅ |
| Decisiones `VIS-*`/`UX-*`, reduced-motion | F4/F9-GATE, `tokens.css` (`prefers-reduced-motion`) | ✅ |
| Responsive mobile/tablet/laptop/desktop | Breakpoints 640/1024/1440 (F4) + E2E en Pixel 7 | ✅ |
| Accesibilidad (teclado, foco, ARIA, contraste) | E2E `a11y.spec.ts`: axe sin violaciones + focus-trap verificado (25 Tab) | ✅ |
| Pruebas pasando con cobertura `TEST-002` | Tabla §3 | ✅ |
| Desplegado en la nube (HTTPS, CORS, Redirect URI prod, logs) | 2026-10-01 sobre `19e9408`: `https://migmusic.vercel.app` + `https://migmusic-api.onrender.com` (health 200 directo y por proxy, preflight 200 con ACAO correcta + credenciales, Spotify acepta la Redirect URI, Render y Vercel auto-desplegaron, `keep-alive.yml` cada 5 min) | ✅ |
| ≥2 funcionalidades adicionales aprobadas e implementadas | `FEAT-001-b/c/d/e` (favoritos, búsqueda, repeat, drag & drop) — 4 de 2 | ✅ |
| Documentación actualizada | README, `docs/architecture.md`, `docs/api.md`, ADR-001..006, este documento | ✅ |
| `F12` — música en segundo plano (Media Session + PWA) | `mediaSession.ts` + `playbackResilience.ts` (7 tests), manifest + service worker sin caché de `/api/*`, iconos generados | ✅ |
| `F12` — arranque inmediato al pulsar una canción | `select` optimista + cancelación de peticiones + iframe de YouTube reutilizado + precarga; E2E `instant-play` mide **clic→título ~115 ms** y que solo suena la última pulsada | ✅ |
| `F13` — letras | `POST /api/lyrics` (YouTube propio → LRCLIB, caché TTL), panel en el reproductor; unit + integración + E2E `lyrics` | ✅ |
| `SEC-001` — rate limiting | Middleware por device-id/IP con buckets default/expensive/auth, 429 + `Retry-After`; `test_security_middleware.py` | ✅ |
| `SEC-001` — validación y cabeceras | `max_length` en schemas, 413 de cuerpo, `X-Device-Id` con formato, cabeceras de seguridad + CSP de página en `vercel.json` | ✅ |
| `SEC-001` — autorización por owner | Todos los endpoints de playlists/playback toman `owner_id` del header validado, nunca del body; SQL `WHERE ... owner_id` | ✅ |
| `SEC-001` — dependencias y secretos | `pip-audit` y `npm audit` sin vulnerabilidades; historial de git sin secretos (nada que rotar) | ✅ |

## 5. Hallazgos (suite E2E y prueba manual en producción)

- **Crash de arranque (F11)**: `hasTrack = playback?.song !== null` daba `true` cuando
  `playback` era `null` (`undefined !== null`), y `App` accedía a `playback.song.title`
  → la app quedaba en blanco en el primer render. Corregido con `!= null`
  (`frontend/src/App.tsx`). Ningún test unitario lo cubría porque los stores se mockean
  poblados: el E2E en navegador real lo detectó en el primer arranque.
- **Colisión de aria-label**: el botón de favorito ("Quitar … de favoritas") y el de borrar
  ("Quitar …") comparten prefijo; los tests E2E usan `data-testid` en lugar de nombre.
- **Click bajo el header sticky (Pixel 7)**: la barra de seek quedaba a 42 px del borde
  superior mientras el header sticky ocupaba 93 px, así que `page.mouse.click` con
  coordenadas crudas disparaba `language-toggle` y el test se quedaba esperando
  `spinbutton "Índice"`. Corregido con `scrollIntoView({ block: "center" })` antes de
  leer `boundingBox()`; un diagnóstico temporal que midió `scrollY`, `barTop` y
  `headerBottom` confirmó la causa y se retiró.
- **Texto suelto en el diálogo de agregar**: la rama de Spotify del `AddTrackDialog`
  dejaba un `)}` huérfano que se pintaba como texto (bug heredado, sin cobertura);
  corregido al migrar el diálogo a Framer Motion.
- **`prefers-reduced-motion` y framer**: `tokens.css` anula las transiciones CSS, pero
  no las animaciones de framer → `MotionConfig reducedMotion="user"` en `main.tsx`
  (`VIS-006`). El drag & drop nativo se cubre ahora con `drag-reorder.spec.ts`
  (eventos sintéticos `dragstart`/`dragover`/`drop` sobre `motion.li`).
- **La búsqueda en Spotify devolvía "Spotify unavailable" (producción)**: el backend
  pedía `limit=20` a `GET /v1/search` y Spotify contesta `400 Invalid limit` por encima
  de 10 resultados (verificado el 2026-10-01 contra la API real, con token de cliente y
  con token de usuario). El manejador traducía ese 400 a `spotify unavailable`, la lista
  salía vacía y daba la impresión de que "no se podía buscar mientras sonaba música
  local" (el diálogo no tiene ninguna dependencia del transporte). Corregido recortando
  el límite a 10 en `SpotifyApiClient.search_tracks` (con reintento a `limit=1` si la
  cota bajara) y registrando el detalle de Spotify en el log del manejador. Smoke real:
  10 canciones para "alvaro diaz".
- **F5 con una pista en marcha**: `attachPlayer` llamaba a `play()` sin gesto de
  usuario y el `NotAllowedError` del navegador aparecía como toast de error
  (`play() failed because the user didn't interact with the document first`).
  Corregido con `isAutoplayBlocked`: se carga en pausa, se muestra el aviso
  informativo `autoplayBlocked` y se sincroniza el backend a `playing=false`.
- **Botón "Agregar" del diálogo Spotify fuera de pantalla**: con una página
  llena de resultados el diálogo crecía más que la ventana y el botón de
  acción quedaba bajo el pliegue. Corregido con `max-height: min(90vh, 90dvh)`
  + cuerpo con scroll y acciones fijas (`Queue.module.css`), y el botón
  muestra el pendiente (`Agregar (n)`); E2E `spotify-dialog.spec.ts`.
- **Siguiente/previous "mueren" en los bordes**: los botones se deshabilitaban
  al llegar al final/inicio y el siguiente clic no explicaba nada. Ahora
  siempre están habilitados y el clic en el borde muestra un toast
  informativo (`player.atEnd`/`player.atStart`) sin cortar la música;
  el seek de ±5 s sustituye al salto de 10 s (`transport-edges.spec.ts`).
- **Playlists sin separar por equipo**: cada equipo veía las listas creadas
  por el resto. Aislamiento por `X-Device-Id` (`UX-010`): solo playlists
  (el reproductor sigue siendo global), sin cabecera ⇒ vista completa para
  no romper E2E/smoke; E2E `device-isolation.spec.ts` con dos contextos.
- **"Siguiente/anterior no cambia nada" (producción y local)**: tras un
  reinicio del backend (Render free se duerme), cualquier llamada al
  transporte contestaba `404 not_found` genérico y la UI se quedaba muda.
  Ahora el backend distingue `404 no_active_playback`, el cliente reconstruye
  el contexto (`open` + `select`) y reintenta una vez; además `GET
  /api/playback` expone `next_index`/`previous_index` para que la UI compute
  el destino optimista. E2E `playback-reload.spec.ts` (recarga con la lista
  reproduciéndose) + unit "PlaybackController resilience" (3 tests: respuesta
  stale descartada, rebuild+retry, playlist borrada).
- **Carrera de respuestas al reportar posición**: dos `POST /playback/report`
  en vuelo se aplicaban en llegada, revirtiendo un `next` reciente. Guarda de
  secuencia por solicitud (`requestSeq`/`lastAppliedSeq`): una respuesta más
  vieja que la última aplicada se descarta sin tocar el store.
- **`activeId` rebotaba a la primera playlist al recargar**: el bootstrap
  reseteaba la selección mientras el backend seguía reproduciendo otra lista;
  ahora se sincroniza `activeId` con `playback.playlist_id` si existe.
- **UI optimista con rollback**: play/pause, seek, ±5 s y siguiente/anterior
  actualizan el store al entrar (el play/pause gira el botón **antes** de que
  el reproductor arranque, con rollback si `play()`/`pause()` falla, y la
  canción se precarga en el reproductor para que suene sin RTT); si la API
  falla, el estado previo se restaura — salvo cuando la respuesta es un
  `no_active_playback` ya recuperado. Unit "PlaybackController optimistic
  UI" (6 tests).
- **`timeupdate` re-renderizaba toda la app (≈4 Hz)**: cada tick recomponía
  el árbol de `App`. El transporte ahora se suscribe por campos (selectors de
  zustand), `position` se cuantiza a segundos enteros (la UI muestra mm:ss),
  `ProgressBar` se suscribe a `position` por su cuenta y las filas/listas/
  controles van con `memo` + drag handlers estables por índice. Sin cambios
  de comportamiento: la misma suite E2E pasa completa.
- **Auto-avance al terminar la pista**: ya existía (`ended` →
  `POST /playback/finished` → `_advance`), pero sin cobertura; ahora lo
  fija `auto-advance.spec.ts` con WAVs de 1 s: la segunda pista arranca
  sola y, en la cola con `repeat=off`, la reproducción se detiene sin
  perder la canción visible.
- **`Spotify player did not report a device id` y transporte "sin vida"**:
  `connect()` del SDK esperaba el evento `ready` con un sondeo de 2 s; si no
  llegaba, `this.player` quedaba apuntando a una instancia sin `_deviceId` y
  el siguiente `ensureConnected` creaba una segunda instancia (fuga), con los
  controles saliendo sin `device_id` o colgados hasta agotar el reintento.
  Ahora el `ready` es event-driven con tope de 10 s (`READY_TIMEOUT_MS`), se
  desconecta el player al fallar, una guarda de `generation` descarta el
  `connect()` cancelado por un `disconnect()` concurrente y los errores
  fatales del SDK (`initialization_error`/`authentication_error`/
  `account_error`) rechazan en el acto en vez de seguir esperando. Además
  `load()` ya no pausa al final (el `attachPlayer` decide play/pause justo
  después) y `play()` no reenvía si ya suena: dos roundtrips SDK menos por
  clic en el transporte. Unit `spotifySdk.test.ts` (6 tests) +
  `SpotifyPlayer.test.ts` actualizados.
- **Botón mudo cuando el backend no contesta**: `apiClient` no tenía timeout,
  así que una petición sin respuesta (Render free se duerme) dejaba el botón
  colgado hasta que el navegador se rendía, sin explicación visible. Ahora
  cada petición aborta a los 10 s (`REQUEST_TIMEOUT_MS`, `AbortController`) y
  el fallo llega como `ApiError code="timeout"` → toast localizado
  `toast.timeout` ("El servidor tardó demasiado en responder") con rollback
  optimista en el transporte (`failureMessage` compartido por los cuatro
  controllers). Unit: `apiClient.test.ts` (timeout con fake timers, timer
  limpio tras el éxito, `failureMessage` es/en) + "PlaybackController
  resilience" (copia localizada en el toast).
- **Respuesta lenta a los botones en producción (frío + parpadeo)**: el
  backend de Render free se dormía entre pings porque el cron de
  `keep-alive.yml` (`*/10`) solo disparó 2 de ~50 runs esperados en 8 h —
  GitHub descarta jobs programados bajo carga, peor en la hora en punto
  (verificado con `GET /actions/runs?event=schedule` → `total_count: 2`;
  medido en frío: health 8,6 s directo y 25 s por el proxy). Ahora el cron
  corre cada 5 min desplazado (`2-59/5 * * * *`, nunca en :00; editar el
  archivo re-registra el schedule) y `App.tsx` hace ping a `/api/health`
  cada 10 min mientras la pestaña está abierta (Render duerme a los 15).
  Observación tras el re-registro (`f51cb79`, 01:45 UTC): los 6 slots
  siguientes (`:47`…`:12`, 01:47–02:12 UTC) tampoco dispararon → el cron
  de GitHub queda como capa de mejores esfuerzos y **la defensa principal
  contra el frío es el ping del cliente** mientras la pestaña está abierta
  (el arranque ya despierta el backend por sí solo); como capa externa
  independiente de GitHub sigue recomendándose UptimeRobot (HANDOFF,
  pendiente de cuenta del usuario).
  Además, un `report` en vuelo iniciado antes del clic se aplicaba después
  del parche optimista y devolvía la UI a la canción vieja mientras la
  nueva ya sonaba: `send()` reserva la secuencia al parchear
  (`lastAppliedSeq = seq`) y `togglePlaying()` reserva antes de
  `await player.play()`, así toda respuesta anterior al clic se descarta.
  Unit "PlaybackController optimistic UI" (+2: canción que no retrocede y
  flip que aguanta durante el arranque de `play()`).
- **Siguiente/anterior sonaba la canción nueva ~2 s y volvía a la vieja**:
  dos vías en `PlaybackController.send`. (1) El `report` de 1 s disparado
  *después* del clic (secuencia mayor) se procesaba en el backend antes de
  que el `next` colgado llegara, devolvía la canción anterior y se aplicaba
  íntegra: la UI y el audio volvían a la vieja. (2) En timeout, el
  `rollback(snapshot)` restauraba la vieja a ciegas aunque el comando
  hubiera aterrizado tarde. Ahora cada `commit()` (next/previous/select/
  seek/skip/finished) abre una ventana de identidad (`intentSeq`): hasta que
  su respuesta asiente, cualquier respuesta —propia o ajena— que apunte a
  otra canción se descarta (y las que corrían dentro de la ventana se
  protegen con `guardBelow` al asentar), y un fallo de desenlace desconocido
  (`timeout`/`network_error`) conserva el estado optimista en lugar de
  hacer rollback: el siguiente `report` reconcilia con la verdad del
  backend (que el comando haya aterrizado o no), con el toast de timeout
   explicando el fallo. Unit "PlaybackController optimistic UI" (+4: report
   con estado viejo durante la ventana, report tardío que aterriza tras la
   respuesta, timeout que conserva la canción nueva, error del servidor que
   sí hace rollback).
- **Correos de fallo de Vercel, lentitud de "Agregar música" y 5xx que
  seguía revirtiendo** (feedback tras FLAP-FIX): (1) un segundo proyecto
  Vercel `frontend` (alias `frontend-miguelceb.vercel.app`, 0 dominios
  custom en la cuenta) estaba conectado al mismo repo y fallaba en cada
  push con `Deployment has failed` ⇒ `vercel project rm frontend`; solo
  queda el productivo `migmusic`, (2) el frío de Render free seguía
  llegando al usuario (el cron de GitHub sigue muerto: 0/6 tras
  re-registro, y el ping de `App.tsx` solo ayuda con la pestaña abierta)
  ⇒ el backend hace su propio ping cada 10 min a
  `RENDER_BACKEND_URL/api/health` desde un task en el lifespan
  (`infrastructure/keep_alive.py`, cancelado en el shutdown), (3) cada
  operación SQL abría una conexión TCP+TLS nueva a Neon (+100-500 ms por
  llamada; el `/playlists` directo promediaba 1,2 s) ⇒ pool
  `psycopg-pool` (min 0 / max 5, commit/rollback por bloque) en
  `SqlPlaylistRepository` y `SqlTokenStore`, con `close()` en el shutdown
  y en los fixtures de integración, (4) el 504/502 del proxy Vercel aún
  hacía rollback a ciegas en el transporte ⇒ `isUnknownOutcome` trata
  `status >= 500` como desenlace desconocido y conserva el optimismo (una
  negativa real es 4xx y sigue revirtiendo: el test del "servidor
  rechaza" pasó de 500 a 400, con 504 y 500 nuevos que conservan).
  Sin bypass del proxy Vercel: la sesión es cookie HttpOnly `mig_session`
  ligada al host, de modo que el tráfico sigue por el proxy. Unit
  `test_keep_alive.py` +4 (URL, pinger, bucle que sobrevive fallos) y
  optimistic UI +2 ⇒ backend **338**, frontend **116**.

## 6. Limitaciones conocidas (sin ocultarlas)

1. **Spotify Premium**: la reproducción con Web Playback SDK solo es verificable con una
   cuenta Premium real → queda para la demo manual (SKILL6 §"Manual guiado"). Sin ella,
   la pestaña Spotify se prueba con dobles.
2. **E2E contra repositorio in-memory**: `DATABASE_URL=""` evita tocar datos reales; la
   fidelidad SQL la dan los tests de contrato con `pgserver` (11 tests, incluido el
   aislamiento por `owner_id`).
3. **Audio real**: el E2E comprueba el ciclo completo sobre un `<audio>` con WAV generado
   y autoplay habilitado por flag de Chromium; la audición por altavoces es manual (demo).
4. **Cobertura de frontend sin gate**: los 116 tests de Vitest no tienen umbral de
   cobertura en CI (el `TEST-002` confirmado aplica al backend).
5. **Auditoría de dependencias**: `npm audit`/`pip-audit` no están como job de CI
   (SKILL6 lo recomienda); ejecutar manualmente antes de publicar.
6. **Demo manual de Spotify pendiente (lo único que queda)**: despliegue y OAuth
   verificados el 2026-10-01 sobre `19e9408` — health 200 directo y por el proxy de
   Vercel, preflight con ACAO correcta, Spotify acepta la Redirect URI registrada y el
   callback reconstruye el login desde el `state` firmado aunque la cookie `mig_oauth`
   no vuelva (422 con cookie y `state` falsificado, 401 sin nada). Auto-deploy de
   Vercel y Render confirmado con ese push y `keep-alive.yml` vigilando `/api/health`.
   No se puede automatizar la autorización con la cuenta Premium del usuario
   (2FA + pantalla de consentimiento): la reproducción con el Web Playback SDK queda
   para la demo guiada (SKILL6 §"Manual guiado").
