# MigMusic 

Reproductor de música web con **lista doblemente enlazada** como núcleo de la arquitectura.
Proyecto académico + producto real — entrega **2026-10-02**.

Reproduce **música local** (archivos del disco, sin subirlos al servidor) y **Spotify**
(OAuth + Web Playback SDK), con playlists persistidas en el servidor y una vista didáctica
de la lista enlazada pensada para la sustentación.

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | Python 3.11+ · FastAPI · uv · Pydantic |
| Base de datos | PostgreSQL (Neon, plan gratuito) |
| Fuentes de audio | HTML5 `<audio>` (local) · Spotify Web Playback SDK |
| Testing | pytest · Vitest · Playwright |
| CI/CD | GitHub Actions (lint + tests que bloquean) |
| Despliegue | Vercel (frontend) · Render (backend) · Neon (DB) |

---

## Arquitectura

Arquitectura **hexagonal por capas** con inyección de dependencias (ADR-001/ADR-002):

```
backend/src/migmusic/
├── core/            # config, logging, excepciones base, seguridad
├── domain/          # reglas puras: Node, DoublyLinkedList, Song, Playlist, ports
├── application/     # casos de uso: PlaylistService, PlaybackService, SpotifyAuthService
├── infrastructure/  # adaptadores: Spotify, persistencia, tokens
└── api/             # routers delgados + schemas + DI + error handlers

frontend/src/
├── domain/          # tipos y contratos
├── players/         # AudioPlayer (abstracto), LocalAudioPlayer, SpotifyPlayer
├── services/        # ApiClient, PlaylistController, PlaybackController
├── storage/         # LocalLibraryRepository (IndexedDB)
└── ui/              # components, layouts, animations, styles (design tokens)
```

**Lista doblemente enlazada (`ARCH-001 = A`):** la DLL vive **solo en el backend Python**.
`Next`/`Previous`/`Skip` son llamadas HTTP al backend, que es quien mantiene el puntero
`current`. El orden se persiste con columnas `prev_id`/`next_id` y la lista se reconstruye
al cargar (`DB-003 = B`).

---

## Requisitos

- Python **3.11+** y [`uv`](https://docs.astral.sh/uv/)
- Node.js **20+** y npm
- Cuenta [Spotify](https://developer.spotify.com/dashboard) con **Premium**
- Una base PostgreSQL (Neon) — opcional durante el desarrollo local

> Sin Docker: el entorno es Windows/VS Code y `DEPLOY-004` quedó rechazado (`CONS-003`).

---

## Variables de entorno

Copia `.env.example` a `.env` y rellena. **Nunca** subas `.env` al repositorio.

| Variable | Descripción |
|---|---|
| `APP_ENV` | `development` / `production` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`… |
| `FRONTEND_ORIGIN` | Origen del frontend (CORS) |
| `ALLOWED_ORIGINS` | Orígenes permitidos, explícitos (nunca `*` con credenciales) |
| `SPOTIFY_CLIENT_ID` | Client ID (público) |
| `SPOTIFY_CLIENT_SECRET` | **Solo backend.** Jamás en chat, código ni frontend |
| `SPOTIFY_REDIRECT_URI` | Debe coincidir **exactamente** con el Dashboard |
| `SESSION_SECRET_KEY` | Firma de cookies de sesión |
| `DATABASE_URL` | URL de conexión a PostgreSQL (Neon) |
| `RENDER_BACKEND_URL` | URL del backend para el proxy `/api/*` de Vercel |

### Configurar la app en Spotify Dashboard

1. Crea la app en <https://developer.spotify.com/dashboard>.
2. **Redirect URIs** (coincidencia exacta, sin barra sobrante):

   | Entorno | URI |
   |---|---|
   | Desarrollo | `http://127.0.0.1:5173/callback` |
   | Producción | `https://migmusic.vercel.app/api/auth/callback` |

   > `localhost` ya **no** es aceptado por Spotify desde el 27/11/2025: usa siempre
   > `127.0.0.1`.
3. Copia el **Client ID** a `SPOTIFY_CLIENT_ID` y el **Client Secret** a
   `SPOTIFY_CLIENT_SECRET` en tu `.env` local y en el panel de Render. No los pegues
   nunca en el chat ni en archivos versionados.
4. **Usuarios de prueba:** en modo *Development* de la app solo funcionan las cuentas
   añadidas manualmente en *Users and access*. Añade tu cuenta y cualquier cuenta que
   vaya a la demo antes de presentar.

---

## Puesta en marcha (desarrollo local)

```powershell
# 1. Backend
cd backend
uv sync
uv run uvicorn migmusic.main:app --reload --port 8000

# 2. Frontend (otra terminal)
cd frontend
npm install
npm run dev          # http://127.0.0.1:5173
```

### Pruebas y lint

```powershell
cd backend
uv run ruff check .
uv run mypy src
uv run pytest          # incluye los tests SQL (PostgreSQL embebido vía pgserver)

cd frontend
npm run lint
npm run test
npm run test:e2e       # Playwright (desktop + móvil + axe); arranca vite y uvicorn solo
```

> La suite E2E necesita el navegador una sola vez: `npx playwright install chromium`.
> No requiere `.env`: el backend de pruebas arranca con valores herméticos y repositorio
> in-memory (nunca toca la base de datos real).
> Estrategia, umbrales y reporte criterio → evidencia: [`docs/testing.md`](docs/testing.md).

> Los tests del adaptador SQL (`tests/integration/test_sql_playlist_repository.py`)
> arrancan un PostgreSQL embebido con `pgserver` (dev dependency, sin Docker). Define
> `TEST_DATABASE_URL` para ejecutarlos contra tu propio servidor (p. ej. Neon).

---

## Despliegue

Topología: **un solo origen**. Vercel sirve el frontend y hace *rewrite* de `/api/*` hacia
el backend en Render.

### Estado actual (2026-09-30)

| Pieza | URL / recurso | Estado |
| --- | --- | --- |
| Frontend (Vercel, proyecto `migmusic`) | <https://migmusic.vercel.app> | ✅ desplegado |
| Backend (Render `migmusic-api`, `srv-dau8psugekts73del56g`) | <https://migmusic-api.onrender.com> | ✅ `live`, health 200 |
| Proxy `/api/*` | <https://migmusic.vercel.app/api/health> | ✅ 200 → Render |
| CORS | preflight con ACAO `https://migmusic.vercel.app` | ✅ 200 |
| BD (Neon, proyecto `MigMusic`) | schema auto-creado en el arranque | ✅ conectada |

Pendiente (acciones del usuario): `SPOTIFY_CLIENT_SECRET` real en Render (hoy placeholder),
registrar la Redirect URI en Spotify Dashboard, y UptimeRobot.
El auto-deploy de Vercel está activo (proyecto con *Root Directory* `frontend`); el de
Render se dispara con `render deploys create` mientras no llegue el webhook de la App de
GitHub.

### 1. Backend en Render

**Opción A — Blueprint (recomendada):** Render → *Blueprints* → conecta el repo;
detecta `render.yaml` en la raíz y crea el servicio con las variables no secretas.

**Opción B — manual:**

1. Conecta el repo de GitHub y crea un **Web Service** con root directory `backend`.
2. Build: `uv sync --frozen` · Start: `uv run uvicorn migmusic.main:app --host 0.0.0.0 --port $PORT`
3. Añade todas las variables del panel (incluido `SPOTIFY_CLIENT_SECRET` y `DATABASE_URL` de Neon).
4. Copia la URL generada (`https://<servicio>.onrender.com`) a `RENDER_BACKEND_URL` **y** al
   destino del rewrite en `frontend/vercel.json`.

### 2. Frontend en Vercel

1. Importa el repo con root directory `frontend` y framework **Vite**.
2. `frontend/vercel.json` ya trae el rewrite de `/api/*` hacia
   `https://migmusic-api.onrender.com` con la cabecera
   **`x-vercel-enable-rewrite-caching: 0`** (ajusta el destino si llamaste al
   servicio de Render de otra forma).
   > Desde el 06/04/2026 Vercel cachea los *rewrites* por defecto: sin esta cabecera el
   > tráfico de `/api/*` puede quedar cacheado en el borde y servir respuestas viejas.
3. Añade `SPOTIFY_REDIRECT_URI=https://migmusic.vercel.app/api/auth/callback` al
   Dashboard **y** las variables de entorno del proyecto.
4. Despliega. Verifica que `/api/health` responde desde `https://migmusic.vercel.app/api/health`.

### 3. Verificación desde CLI

```bash
# Últimos deploys de Render (estado live / build_failed)
render deploys list srv-dau8psugekts73del56g

# Salud del backend y del proxy de un solo origen
curl https://migmusic-api.onrender.com/api/health
curl https://migmusic.vercel.app/api/health
```

### 4. Cold start

Render apaga el servicio en planes gratuitos. Un *ping* de
[UptimeRobot](https://uptimerobot.com/) cada 5 minutos a `/api/health` evita la primera
petición lenta. Configuración usada: monitor **HTTP(s)**, nombre `MigMusic API`,
URL `https://migmusic-api.onrender.com/api/health`, intervalo **5 min**.

### Rollback

- **Vercel:** pestaña *Deployments* → *Promote to Production* en el último deployment sano.
- **Render:** *Deploys* → *Rollback* al commit anterior.
- **Neon:** *Restore* a un punto anterior de la rama `main`.
- Migraciones reversibles: nunca despliegues una migración destructiva sin backup.

---

## Estructura del repositorio

```
migmusic/
├── AGEND.md            # fuente de verdad del proyecto (requisitos + decisiones)
├── skills/             # skills del agente (SKILL0–SKILL7)
├── README.md
├── .env.example
├── .github/workflows/  # CI: lint + tests que bloquean
├── docs/
│   ├── architecture.md # capas + diagramas Mermaid (clases, secuencia, ER)
│   ├── adr/            # Architecture Decision Records
│   ├── api.md
│   └── testing.md      # estrategia de pruebas + reporte criterio → evidencia
├── backend/            # 100 % Python
│   ├── pyproject.toml  # uv · ruff · mypy estricto · pytest
│   ├── src/migmusic/
│   └── tests/          # unit / integration / conftest.py
├── frontend/           # React + Vite + TypeScript
│   ├── package.json
│   ├── vercel.json     # rewrite /api/* → Render (un solo origen)
│   ├── e2e/            # Playwright: smoke, flujo maestro, accesibilidad (axe)
│   └── src/
└── render.yaml         # blueprint de Render: Web Service + variables
```

---

## Roadmap

| Fase | Contenido |
|---|---|
| F0 | Entrevista y gate de implementación ✅ |
| F1 | Fundaciones: repo, estructura, tooling, config, logging, CI |
| F2 | Núcleo de dominio: `Node`, `DoublyLinkedList`, `Song`, `Playlist` |
| F3 | Servicios y API |
| F4 | Frontend base: layout, tokens, componentes |
| F5 | Audio local |
| F6 | Spotify (OAuth + Web Playback SDK) |
| F7 | Integración y vista didáctica de la lista |
| F8 | Funcionalidades adicionales (favoritos, búsqueda, repeat, drag&drop) |
| F9 | Pulido: animaciones, responsive, accesibilidad |
| F10 | Despliegue |
| F11 | Cierre: E2E, documentación, demo |

---

## Licencia

Proyecto académico. Todos los derechos reservados.
