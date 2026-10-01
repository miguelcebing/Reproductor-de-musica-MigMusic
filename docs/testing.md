# Estrategia y reporte de pruebas (F11)

> Fuente de verdad de calidad: `AGEND.md` (`TEST-001..004`) y `skills/SKILL6.md`.
> Actualizado: 2026-10-01 (OAuth, música local tras F5 y Framer Motion).

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

# Frontend (desde frontend/)
npm run lint ; npm run typecheck
npm run test -- --run        # Vitest
npm run build
npm run test:e2e             # Playwright; una vez: npx playwright install chromium
```

La suite E2E es hermética: no necesita `.env`, arranca Vite (5173) y Uvicorn (8000) sola,
fuerza `DATABASE_URL=""` (repositorio in-memory, nunca toca una base real) y resetea los
playlists vía API en cada test.

## 3. Estado actual (2026-10-01)

| Métrica | Umbral (`TEST-002`) | Actual |
|---|---|---|
| Cobertura global backend | ≥ 80 % | **96.83 %** |
| Cobertura `domain/` | ≥ 95 % | **100 %** |
| Tests backend | — | **309** (unit + integración + property-based) |
| Tests frontend (Vitest) | — | **77** (8 archivos) |
| Tests E2E (Playwright) | — | **9** (5 specs: smoke, maestro, drag & drop, persistencia local, axe) |
| Violaciones axe (WCAG 2.1 A/AA) | 0 | **0** (light, dark y diálogo abierto) |
| Jobs de CI (`TEST-003`) | bloquean | `backend`, `frontend`, `e2e`, `no-secrets` |

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
| Desplegado en la nube (HTTPS, CORS, Redirect URI prod, logs) | 2026-09-30: `https://migmusic.vercel.app` + `https://migmusic-api.onrender.com` (health 200, proxy `/api/health` 200, CORS preflight 200 con ACAO correcto, Neon conectado, auto-deploy Render `trigger=commit`). Falta acción del usuario: secret real de Spotify + redirect URI en Spotify Dashboard | ⚠️ |
| ≥2 funcionalidades adicionales aprobadas e implementadas | `FEAT-001-b/c/d/e` (favoritos, búsqueda, repeat, drag & drop) — 4 de 2 | ✅ |
| Documentación actualizada | README, `docs/architecture.md`, `docs/api.md`, ADR-001..006, este documento | ✅ |

## 5. Hallazgos de la suite E2E

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

## 6. Limitaciones conocidas (sin ocultarlas)

1. **Spotify Premium**: la reproducción con Web Playback SDK solo es verificable con una
   cuenta Premium real → queda para la demo manual (SKILL6 §"Manual guiado"). Sin ella,
   la pestaña Spotify se prueba con dobles.
2. **E2E contra repositorio in-memory**: `DATABASE_URL=""` evita tocar datos reales; la
   fidelidad SQL la dan los tests de contrato con `pgserver` (8 tests).
3. **Audio real**: el E2E comprueba el ciclo completo sobre un `<audio>` con WAV generado
   y autoplay habilitado por flag de Chromium; la audición por altavoces es manual (demo).
4. **Cobertura de frontend sin gate**: los 77 tests de Vitest no tienen umbral de
   cobertura en CI (el `TEST-002` confirmado aplica al backend).
5. **Auditoría de dependencias**: `npm audit`/`pip-audit` no están como job de CI
   (SKILL6 lo recomienda); ejecutar manualmente antes de publicar.
6. **Despliegue ejecutado, configuración parcial de Spotify pendiente**: el despliegue real se hizo
   el 2026-09-30 (Vercel `migmusic` con Root Directory `frontend`, Render `migmusic-api`,
   Neon `MigMusic`; health, proxy y CORS verificados; auto-deploy de Vercel activo).
   Quedan acciones del usuario: `SPOTIFY_CLIENT_SECRET` real en Render (hoy placeholder),
   registrar la Redirect URI en Spotify Dashboard y el webhook de Render en GitHub;
   hasta entonces OAuth no es utilizable en producción.
