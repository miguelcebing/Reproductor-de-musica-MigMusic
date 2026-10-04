# MigMusic 

Reproductor de mÃºsica web con **lista doblemente enlazada** como nÃºcleo de la arquitectura.
Proyecto acadÃ©mico + producto real â€” entrega **2026-10-02**.

Reproduce **mÃºsica local** (archivos del disco, sin subirlos al servidor) y **Spotify**
(OAuth + Web Playback SDK), con playlists persistidas en el servidor y una vista didÃ¡ctica
de la lista enlazada pensada para la sustentaciÃ³n.

---

## Stack

| Capa | TecnologÃ­a |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | Python 3.11+ Â· FastAPI Â· uv Â· Pydantic |
| Base de datos | PostgreSQL (Neon, plan gratuito) |
| Fuentes de audio | HTML5 `<audio>` (local) Â· Spotify Web Playback SDK |
| Testing | pytest Â· Vitest Â· Playwright |
| Animaciones | Framer Motion (`MotionConfig reducedMotion="user"`) |
| CI/CD | GitHub Actions (lint + tests que bloquean + *keep-alive* cada 10 min) |
| Despliegue | Vercel (frontend) Â· Render (backend) Â· Neon (DB) |

---

## Arquitectura

Arquitectura **hexagonal por capas** con inyecciÃ³n de dependencias (ADR-001/ADR-002):

```
backend/src/migmusic/
â”œâ”€â”€ core/            # config, logging, excepciones base, seguridad
â”œâ”€â”€ domain/          # reglas puras: Node, DoublyLinkedList, Song, Playlist, ports
â”œâ”€â”€ application/     # casos de uso: PlaylistService, PlaybackService, SpotifyAuthService
â”œâ”€â”€ infrastructure/  # adaptadores: Spotify, persistencia, tokens
â””â”€â”€ api/             # routers delgados + schemas + DI + error handlers

frontend/src/
â”œâ”€â”€ domain/          # tipos y contratos
â”œâ”€â”€ players/         # AudioPlayer (abstracto), LocalAudioPlayer, SpotifyPlayer
â”œâ”€â”€ services/        # ApiClient, PlaylistController, PlaybackController
â”œâ”€â”€ storage/         # LocalLibraryRepository (IndexedDB)
â””â”€â”€ ui/              # components, layouts, animations, styles (design tokens)
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
- Una base PostgreSQL (Neon) â€” opcional durante el desarrollo local

> Sin Docker: el entorno es Windows/VS Code y `DEPLOY-004` quedÃ³ rechazado (`CONS-003`).

---

## Variables de entorno

Copia `.env.example` a `.env` y rellena. **Nunca** subas `.env` al repositorio.

| Variable | DescripciÃ³n |
|---|---|
| `APP_ENV` | `development` / `production` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`â€¦ |
| `FRONTEND_ORIGIN` | Origen del frontend (CORS) |
| `ALLOWED_ORIGINS` | OrÃ­genes permitidos, explÃ­citos (nunca `*` con credenciales) |
| `SPOTIFY_CLIENT_ID` | Client ID (pÃºblico) |
| `SPOTIFY_CLIENT_SECRET` | **Solo backend.** JamÃ¡s en chat, cÃ³digo ni frontend |
| `SPOTIFY_REDIRECT_URI` | Debe coincidir **exactamente** con el Dashboard |
| `SESSION_SECRET_KEY` | Firma de cookies de sesiÃ³n y del `state` OAuth |
| `OAUTH_STATE_MAX_AGE` | Segundos que puede durar un login sin terminar (defecto `900`) |
| `DATABASE_URL` | URL de conexiÃ³n a PostgreSQL (Neon) |
| `RENDER_BACKEND_URL` | URL del backend para el proxy `/api/*` de Vercel |
| `RATE_LIMIT_ENABLED` | Activa el rate limiting (por defecto `true`; `false` en desarrollo/tests) |
| `RATE_LIMIT_DEFAULT_PER_MINUTE` | Presupuesto general por minuto (defecto `120`) |
| `RATE_LIMIT_EXPENSIVE_PER_MINUTE` | Presupuesto estricto de bÃºsqueda/letras/YouTube (defecto `20`) |
| `RATE_LIMIT_AUTH_PER_MINUTE` | Presupuesto de `/api/auth/*` (defecto `10`) |
| `MAX_REQUEST_BODY_BYTES` | TamaÃ±o mÃ¡ximo de cuerpo; por encima responde `413` (defecto `65536`) |
| `TRUSTED_HOSTS` | Lista de Host permitidos (opcional; por defecto localhost + `*.onrender.com`) |

### Configurar la app en Spotify Dashboard

1. Crea la app en <https://developer.spotify.com/dashboard>.
2. **Redirect URIs** (coincidencia exacta, sin barra sobrante):

   | Entorno | URI |
   |---|---|
   | Desarrollo | `http://127.0.0.1:5173/callback` |
   | ProducciÃ³n | `https://migmusic.vercel.app/api/auth/callback` |

   > `localhost` ya **no** es aceptado por Spotify desde el 27/11/2025: usa siempre
   > `127.0.0.1`.
3. Copia el **Client ID** a `SPOTIFY_CLIENT_ID` y el **Client Secret** a
   `SPOTIFY_CLIENT_SECRET` en tu `.env` local y en el panel de Render. No los pegues
   nunca en el chat ni en archivos versionados.
4. **Usuarios de prueba:** en modo *Development* de la app solo funcionan las cuentas
   aÃ±adidas manualmente en *Users and access*. AÃ±ade tu cuenta y cualquier cuenta que
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
uv run pytest          # incluye los tests SQL (PostgreSQL embebido vÃ­a pgserver)
uv run pip-audit --skip-editable   # auditorÃ­a de dependencias (0 vulnerabilidades)

cd frontend
npm run lint
npm run test
npm run test:e2e       # Playwright (desktop + mÃ³vil + axe); arranca vite y uvicorn solo
```

> La suite E2E necesita el navegador una sola vez: `npx playwright install chromium`.
> No requiere `.env`: el backend de pruebas arranca con valores hermÃ©ticos y repositorio
> in-memory (nunca toca la base de datos real).
> Estrategia, umbrales y reporte criterio â†’ evidencia: [`docs/testing.md`](docs/testing.md).

> Los tests del adaptador SQL (`tests/integration/test_sql_playlist_repository.py`)
> arrancan un PostgreSQL embebido con `pgserver` (dev dependency, sin Docker). Define
> `TEST_DATABASE_URL` para ejecutarlos contra tu propio servidor (p. ej. Neon).

---

## Despliegue

TopologÃ­a: **un solo origen**. Vercel sirve el frontend y hace *rewrite* de `/api/*` hacia
el backend en Render.

### Estado actual (2026-09-30)

| Pieza | URL / recurso | Estado |
| --- | --- | --- |
| Frontend (Vercel, proyecto `migmusic`) | <https://migmusic.vercel.app> | âœ… desplegado |
| Backend (Render `migmusic-api`, `srv-dauk5k8jo6nc73dgl7ug`) | <https://migmusic-api.onrender.com> | âœ… `live`, health 200 |
| Proxy `/api/*` | <https://migmusic.vercel.app/api/health> | âœ… 200 â†’ Render |
| CORS | preflight con ACAO `https://migmusic.vercel.app` | âœ… 200 |
| BD (Neon, proyecto `MigMusic`) | schema auto-creado en el arranque | âœ… conectada |

Verificado el 2026-10-01: health 200 directo y por el proxy, CORS con credenciales,
Redirect URI aceptada por Spotify y auto-deploy de Vercel y Render con el Ãºltimo push.
El *keep-alive* ya no depende de un servicio externo: el workflow `keep-alive.yml` de
GitHub Actions pinga `/api/health` cada 10 minutos.
Queda solo la demo manual con cuenta Premium (autorizar y reproducir con el Web
Playback SDK).
El auto-deploy de Vercel estÃ¡ activo (proyecto con *Root Directory* `frontend`); el de
Render se dispara con `render deploys create` mientras no llegue el webhook de la App de
GitHub.

### 1. Backend en Render

**OpciÃ³n A â€” Blueprint (recomendada):** Render â†’ *Blueprints* â†’ conecta el repo;
detecta `render.yaml` en la raÃ­z y crea el servicio con las variables no secretas.

**OpciÃ³n B â€” manual:**

1. Conecta el repo de GitHub y crea un **Web Service** con root directory `backend`.
2. Build: `uv sync --frozen` Â· Start: `uv run uvicorn migmusic.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`
   (las cabeceras `X-Forwarded-*` que manda Vercel son las que dan el esquema y el host
   reales a las redirecciones y a las cookies `Secure`).
3. AÃ±ade todas las variables del panel (incluido `SPOTIFY_CLIENT_SECRET` y `DATABASE_URL` de Neon).
4. Copia la URL generada (`https://<servicio>.onrender.com`) a `RENDER_BACKEND_URL` **y** al
   destino del rewrite en `frontend/vercel.json`.

### 2. Frontend en Vercel

1. Importa el repo con root directory `frontend` y framework **Vite**.
2. `frontend/vercel.json` ya trae el rewrite de `/api/*` hacia
   `https://migmusic-api.onrender.com` con la cabecera
   **`x-vercel-enable-rewrite-caching: 0`** (ajusta el destino si llamaste al
   servicio de Render de otra forma).
   > Desde el 06/04/2026 Vercel cachea los *rewrites* por defecto: sin esta cabecera el
   > trÃ¡fico de `/api/*` puede quedar cacheado en el borde y servir respuestas viejas.
   > El segundo rewrite (`/(.*)` â†’ `/index.html`) es el *catch-all* del SPA: sin Ã©l,
   > el callback de OAuth y los enlaces profundos contestan `404` en Vercel.
3. AÃ±ade `SPOTIFY_REDIRECT_URI=https://migmusic.vercel.app/api/auth/callback` al
   Dashboard **y** las variables de entorno del proyecto.
4. Despliega. Verifica que `/api/health` responde desde `https://migmusic.vercel.app/api/health`.

### 3. VerificaciÃ³n desde CLI

```bash
# Ãšltimos deploys de Render (estado live / build_failed)
render deploys list srv-dauk5k8jo6nc73dgl7ug

# Salud del backend y del proxy de un solo origen
curl https://migmusic-api.onrender.com/api/health
curl https://migmusic.vercel.app/api/health
```

### 4. Cold start y monitorizaciÃ³n

Render apaga el servicio en planes gratuitos. El workflow
[`.github/workflows/keep-alive.yml`](.github/workflows/keep-alive.yml) pinga
`https://migmusic-api.onrender.com/api/health` cada 10 minutos (`schedule` +
`workflow_dispatch`), reintenta hasta 90 s para absorber el arranque en frÃ­o y despuÃ©s
comprueba el mismo health a travÃ©s del proxy de Vercel. A la vez es *keep-alive* y
monitor de producciÃ³n: si responde 200, el flujo completo (navegador â†’ Vercel â†’ Render)
estÃ¡ vivo.

> GitHub desactiva los `schedule` de un repositorio sin actividad durante 60 dÃ­as;
> un commit o un disparo manual del workflow lo vuelve a activar.

### Rollback

- **Vercel:** pestaÃ±a *Deployments* â†’ *Promote to Production* en el Ãºltimo deployment sano.
- **Render:** *Deploys* â†’ *Rollback* al commit anterior.
- **Neon:** *Restore* a un punto anterior de la rama `main`.
- Migraciones reversibles: nunca despliegues una migraciÃ³n destructiva sin backup.

---

## Estructura del repositorio

```
migmusic/
â”œâ”€â”€ AGEND.md            # fuente de verdad del proyecto (requisitos + decisiones)
â”œâ”€â”€ docs/skills/             # skills del agente (SKILL0â€“SKILL7)
â”œâ”€â”€ README.md
â”œâ”€â”€ .env.example
â”œâ”€â”€ .github/workflows/  # CI: lint + tests que bloquean + keep-alive
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ architecture.md # capas + diagramas Mermaid (clases, secuencia, ER)
â”‚   â”œâ”€â”€ adr/            # Architecture Decision Records
â”‚   â”œâ”€â”€ api.md
â”‚   â””â”€â”€ testing.md      # estrategia de pruebas + reporte criterio â†’ evidencia
â”œâ”€â”€ backend/            # 100 % Python
â”‚   â”œâ”€â”€ pyproject.toml  # uv Â· ruff Â· mypy estricto Â· pytest
â”‚   â”œâ”€â”€ src/migmusic/
â”‚   â””â”€â”€ tests/          # unit / integration / conftest.py
â”œâ”€â”€ frontend/           # React + Vite + TypeScript
â”‚   â”œâ”€â”€ package.json
â”‚   â”œâ”€â”€ vercel.json     # rewrite /api/* â†’ Render (un solo origen)
â”‚   â”œâ”€â”€ e2e/            # Playwright: smoke, maestro, drag & drop, persistencia, axe
â”‚   â””â”€â”€ src/
â””â”€â”€ render.yaml         # blueprint de Render: Web Service + variables
```

---

## Roadmap

| Fase | Contenido |
|---|---|
| F0 | Entrevista y gate de implementaciÃ³n âœ… |
| F1 | Fundaciones: repo, estructura, tooling, config, logging, CI |
| F2 | NÃºcleo de dominio: `Node`, `DoublyLinkedList`, `Song`, `Playlist` |
| F3 | Servicios y API |
| F4 | Frontend base: layout, tokens, componentes |
| F5 | Audio local |
| F6 | Spotify (OAuth + Web Playback SDK) |
| F7 | IntegraciÃ³n y vista didÃ¡ctica de la lista |
| F8 | Funcionalidades adicionales (favoritos, bÃºsqueda, repeat, drag&drop) |
| F9 | Pulido: animaciones, responsive, accesibilidad |
| F10 | Despliegue |
| F11 | Cierre: E2E, documentaciÃ³n, demo |

---

## Licencia

Proyecto acadÃ©mico. Todos los derechos reservados.
