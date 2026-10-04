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
| CI/CD | GitHub Actions (lint + tests que bloquean) |
| Despliegue | AWS EC2 (frontend + backend, `us-east-1`) Â· Neon (DB) Â· DuckDNS + Let's Encrypt (dominio y HTTPS) |

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
| `RATE_LIMIT_ENABLED` | Activa el rate limiting (por defecto `true`; `false` en desarrollo/tests) |
| `RATE_LIMIT_DEFAULT_PER_MINUTE` | Presupuesto general por minuto (defecto `120`) |
| `RATE_LIMIT_EXPENSIVE_PER_MINUTE` | Presupuesto estricto de bÃºsqueda/letras/YouTube (defecto `20`) |
| `RATE_LIMIT_AUTH_PER_MINUTE` | Presupuesto de `/api/auth/*` (defecto `10`) |
| `MAX_REQUEST_BODY_BYTES` | TamaÃ±o mÃ¡ximo de cuerpo; por encima responde `413` (defecto `65536`) |
| `TRUSTED_HOSTS` | Lista de Host permitidos (opcional; por defecto localhost + `*.onrender.com`) |
| `YOUTUBE_MUSIC_ENABLED` | Activa la búsqueda en YouTube Music (defecto `true`) |

### Configurar la app en Spotify Dashboard

1. Crea la app en <https://developer.spotify.com/dashboard>.
2. **Redirect URIs** (coincidencia exacta, sin barra sobrante):

   | Entorno | URI |
   |---|---|
   | Desarrollo | `http://127.0.0.1:5173/callback` |
   | ProducciÃ³n | `https://migmusicreproductor.duckdns.org/api/auth/callback` |

   > `localhost` ya **no** es aceptado por Spotify desde el 27/11/2025: usa siempre
   > `127.0.0.1`. En producciÃ³n Spotify exige **HTTPS**.
3. Copia el **Client ID** a `SPOTIFY_CLIENT_ID` y el **Client Secret** a
   `SPOTIFY_CLIENT_SECRET` en tu `.env` local y en `/etc/migmusic/migmusic.env` del servidor.
   No los pegues nunca en el chat ni en archivos versionados.
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

TopologÃ­a: **un servidor** (AWS EC2) que sirve la SPA y hace *reverse proxy* de `/api/*`
hacia Gunicorn en `127.0.0.1:8000`. La DB sigue en Neon; el dominio y el TLS los aportan
DuckDNS y Let's Encrypt. Un solo origen, asÃ­ que las cookies de sesiÃ³n viajan siempre
*first-party* y el OAuth no depende de un proxy externo.

```
  navegador
     â”‚  HTTPS (443)
     â–¼
  Nginx  â”€â”€â”€â”€ /assets, /icons, /  â”€â”€â”€â”€â–º  /opt/migmusic/frontend/dist   (SPA)
  EC2    â”€â”€â”€â”€ /api/, /health      â”€â”€â”€â”€â–º  Gunicorn 127.0.0.1:8000     (FastAPI)
     â”‚                                       â”‚
     â””â”€â”€ Let's Encrypt (certbot, renovaciÃ³n automÃ¡tica)
                                             â–¼
                                    Neon PostgreSQL (us-east-2)
```

### Estado actual (2026-10-04)

| Pieza | URL / recurso | Estado |
| --- | --- | --- |
| App completa (SPA + API) | <https://migmusicreproductor.duckdns.org> | âœ… HTTPS 200 |
| Health | <https://migmusicreproductor.duckdns.org/api/health> | âœ… `{"status":"ok","environment":"production"}` |
| HTTP â†’ HTTPS | `http://migmusicreproductor.duckdns.org` | âœ… `301` permanente |
| Certificado | Let's Encrypt, renovaciÃ³n por `certbot.timer` | âœ… vÃ¡lido, `dry-run` OK |
| Instancia | EC2 `i-0c4b5c163d93e48a2` (`t3.micro`, us-east-1) + IP elÃ¡stica `54.166.184.47` | âœ… running |
| BD (Neon, proyecto `MigMusic`) | schema auto-creado en el arranque | âœ… conectada |
| Presupuesto | AWS Budgets `migmusic-monthly` (10 USD/mes, alertas 5 y 10) | âœ… activo |

Verificado el 2026-10-04: reinicio completo del servidor con recuperaciÃ³n automÃ¡tica en
~30 s, round-trip real contra Neon (crear â†’ listar â†’ borrar playlist), letras (lrclib) y
bÃºsqueda de YouTube Music funcionando desde el servidor, y 411 tests backend + 152
frontend en verde sobre un clon limpio.

Queda pendiente solo la **demo manual con cuenta Premium** (autorizar y reproducir con el
Web Playback SDK): no se puede automatizar por el 2FA y la pantalla de consentimiento.

### Desplegar un cambio

Todo el ciclo vive en `infra/`:

```powershell
# 1. Provisionar el servidor (una sola vez; es idempotente)
bash infra/scripts/provision.sh

# 2. Construir y subir (empaqueta, sube, uv sync, nginx, systemd, health check)
.\infra\scripts\deploy.ps1 -Target 54.166.184.47
#    -SkipBuild  reutiliza el frontend/dist ya construido
```

`deploy.ps1` empaqueta el repo, lo sube por SSH, instala el entorno con `uv sync --frozen`
y ejecuta `apply-deploy.sh`, que valida `/health` con reintentos antes de dar por bueno el
despliegue. Los secretos **no** viajan en el paquete: viven en
`/etc/migmusic/migmusic.env` (`root:migmusic`, `0640`).

### Primer arranque del servidor (resumen)

1. `provision.sh`: usuario de servicio `migmusic`, nginx, certbot, fail2ban, ufw
   (solo 22 desde la IP del admin + 80/443), swap de 2 GB, `uv`, cliente de PostgreSQL.
2. `/etc/migmusic/migmusic.env` con los 21 valores (`infra/env/migmusic.env.example`).
3. `deploy.ps1 -Target <ip>`.
4. `certbot --nginx -d migmusicreproductor.duckdns.org --redirect`.
5. Actualizar el **Redirect URI** en el Dashboard de Spotify (ver arriba).

### OperaciÃ³n

```bash
# Logs en vivo (una lÃnea JSON por evento)
journalctl -u migmusic -f

# Estado de los servicios
systemctl status migmusic nginx
systemctl list-timers            # backup nocturno y renovaciÃ³n del certificado

# Backup manual de la base de datos (el timer lo hace cada noche)
sudo systemctl start migmusic-backup.service
```

### Rollback

- **App:** volver a un commit anterior y re-ejecutar `deploy.ps1` (el despliegue es
  atÃ³mico a nivel de release: el health check decide si se mantiene).
- **Neon:** *Restore* a un punto anterior de la rama `main`, o restaurar el volcado
  nocturno que genera `migmusic-backup.timer`.
- Migraciones reversibles: nunca despliegues una migraciÃ³n destructiva sin backup.

> Los archivos `render.yaml`, `.github/workflows/keep-alive.yml` y `frontend/vercel.json`
> pertenecen a la topologÃ­a antigua (Vercel + Render) y se retiraron al migrar a AWS
> (`DEPLOY-006`). Si necesitas volver a ellos, estÃ¡n en el historial de Git.

---

## Estructura del repositorio

```
migmusic/
â”œâ”€â”€ AGEND.md            # fuente de verdad del proyecto (requisitos + decisiones)
â”œâ”€â”€ docs/skills/             # skills del agente (SKILL0â€“SKILL7)
â”œâ”€â”€ README.md
â”œâ”€â”€ .env.example
â”œâ”€â”€ .github/workflows/  # CI: lint + tests que bloquean
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
â”‚   â”œâ”€â”€ e2e/            # Playwright: smoke, maestro, drag & drop, persistencia, axe
â”‚   â””â”€â”€ src/
â””â”€â”€ infra/              # despliegue en AWS (ver infra/README.md)
    â”œâ”€â”€ nginx/          # vhost + cabeceras de seguridad
    â”œâ”€â”€ systemd/        # migmusic.service, backup nocturno
    â”œâ”€â”€ gunicorn/       # configuraciÃ³n del WSGI
    â”œâ”€â”€ env/            # plantilla de variables (sin valores)
    â”œâ”€â”€ iam/            # polÃ­tica least-privilege del despliegue
    â””â”€â”€ scripts/        # provision.sh, deploy.ps1, apply-deploy.sh, backup-db.sh
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
