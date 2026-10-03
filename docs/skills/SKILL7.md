---
name: deployment-cloud
description: Despliega MigMusic en la nube (frontend + backend Python) con HTTPS, variables de entorno, CORS, cookies, Spotify Redirect URI de producción, logs y configuración de producción. Úsala tras confirmar DEPLOY-*.
---

# Skill: deployment-cloud

## Responsabilidad única

Llevar MigMusic a producción de forma **segura, reproducible y observable**. No define la lógica de negocio; asegura que lo construido funciona fuera del equipo local.

## Precondiciones (AGEND.md)

`DEPLOY-001`, `DEPLOY-002` (críticas); `DEPLOY-003..005`; `SPOTIFY-003`, `SPOTIFY-004`; `DB-001..003` si hay base de datos; `CONS-005` (presupuesto). Fases F1–F9 con pruebas verdes.

## Verificación de plataforma vigente

Precios, planes gratuitos, arranque en frío, disco efímero y límites cambian. Antes de recomendar o desplegar, consultar la documentación actual de la plataforma elegida y registrar en un ADR: costos, límites, región, política de sleep/idle, y cómo se gestionan secretos.

## Topologías (para recomendar en `DEPLOY-001` / `DEPLOY-002`)

| Opción | Descripción | Pros | Contras |
|---|---|---|---|
| **A. Front estático + API Python separados** | Frontend en Vercel/Netlify/Cloudflare Pages; backend en Render/Railway/Fly.io | Escalado independiente; CDN para el front; planes gratuitos frecuentes | CORS y cookies cross-site (`SameSite=None; Secure`); dos dominios |
| **B. Todo bajo un dominio (reverse proxy)** | El backend sirve la API en `/api` y los estáticos, o un proxy los unifica | Sin CORS ni problemas de cookies; Redirect URI simple | Un solo servicio; menos independencia |
| **C. Contenedor único (Docker)** | Imagen que incluye backend y build del frontend | Reproducible; portable | Menos optimización de CDN |
| **D. IaaS/PaaS grande (AWS/Azure/GCP)** | ECS/App Service/Cloud Run + CDN + DB gestionada | Control y escalado | Complejidad y costo |

Recomendación de partida (confirmar): **B o A con subdominios del mismo sitio** para simplificar cookies de sesión y OAuth; **Docker** para consistencia; PostgreSQL gestionado solo si `DB-001` lo exige.

## Configuración de producción

**Variables de entorno (en el panel del proveedor, nunca en el repo):**
```
APP_ENV=production
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=https://<prod-domain>/auth/spotify/callback
SESSION_SECRET_KEY=
FRONTEND_ORIGIN=https://<prod-front-domain>
ALLOWED_ORIGINS=https://<prod-front-domain>
DATABASE_URL=          # si aplica
LOG_LEVEL=INFO
```
- `Settings` falla al arrancar si falta algo obligatorio.
- Modo debug **desactivado**; documentación interactiva de la API restringida o protegida.
- Servidor de producción: ASGI/WSGI apropiado (p. ej. `uvicorn`/`gunicorn` con workers) — no el servidor de desarrollo.
- Respetar el puerto que inyecta la plataforma (`PORT`).
- `X-Forwarded-*`/proxy headers de confianza configurados para que las URLs generadas sean `https`.

## HTTPS y seguridad de transporte

- HTTPS obligatorio (lo suele proveer la plataforma); redirigir HTTP → HTTPS; HSTS.
- Cookies de sesión: `Secure`, `HttpOnly`, `SameSite` acorde a `DEPLOY-002`.
- Cabeceras: `Content-Security-Policy` (permitir `sdk.scdn.co` y orígenes de portadas de Spotify), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. Las políticas de audio/EME deben permitir el funcionamiento del SDK.

## CORS

- Orígenes **explícitos** (`ALLOWED_ORIGINS`), nunca `*` con credenciales.
- Métodos y cabeceras mínimas; `allow_credentials=true` solo si el front está en otro origen.
- Probar preflight (`OPTIONS`) y errores CORS desde el navegador.

## Spotify en producción

1. Añadir la Redirect URI de producción en el Dashboard (coincidencia **exacta**: protocolo, dominio, ruta, sin barra sobrante).
2. Verificar en la documentación vigente las reglas de HTTPS/loopback y el modo de la app (desarrollo vs. cuota extendida): en modo desarrollo solo funcionan usuarios añadidos manualmente → documentar en el README cómo añadir usuarios de prueba.
3. Probar el ciclo completo en producción: login → callback → reproducir → esperar refresh → logout.

## Base de datos (si aplica)

- Instancia gestionada con backups; migraciones automatizadas (Alembic/Django migrations) ejecutadas en el despliegue.
- **SQLite en cloud:** cuidado con discos efímeros (se pierde el archivo en cada redeploy) → solo con volumen persistente.
- Conexiones con TLS; usuario con privilegios mínimos.

## Build y CI/CD (`DEPLOY-003`, `DEPLOY-004`)

- **Docker** multi-stage para backend (imagen pequeña, usuario no root, healthcheck) y build del frontend con hash de assets.
- GitHub Actions: lint + tests → build → despliegue a *staging* → smoke tests → *production* (manual o automático).
- Entornos separados: `development`, `staging` (opcional), `production`, cada uno con sus credenciales de Spotify/Redirect URI.
- Versionado de releases y rollback documentado.

## Logs y observabilidad (`DEPLOY-005`)

- Logs estructurados (JSON) a stdout; correlación con `request_id`.
- **Nunca** registrar tokens, cookies, Client Secret ni cuerpos con datos sensibles.
- `GET /health` (liveness) y `GET /ready` (dependencias) para la plataforma.
- Métricas/alertas básicas (errores 5xx, latencia, fallos de OAuth); Sentry o equivalente si el usuario lo aprueba.

## Smoke tests posteriores al despliegue

- [ ] `GET /health` responde 200 sobre HTTPS.
- [ ] La app carga sin errores de consola/CSP.
- [ ] CORS correcto desde el dominio del frontend.
- [ ] Login de Spotify completa y vuelve a la app.
- [ ] Reproducción con Spotify (cuenta Premium) y con archivo local.
- [ ] Add/remove/next/previous/skip ± N s operan.
- [ ] Logs visibles y sin datos sensibles.
- [ ] Responsive verificado en móvil real.

## Entregables

- `deploy/` con configuración (Dockerfile, compose, manifiestos de la plataforma).
- `README` con: variables requeridas, pasos de despliegue, cómo configurar Spotify Dashboard, cómo hacer rollback.
- ADR de la plataforma elegida.
- `AGEND.md` actualizado (Decision Log, criterios de aceptación de despliegue).

## Definición de terminado

- [ ] Aplicación accesible por HTTPS en una URL pública.
- [ ] Variables de entorno configuradas; ningún secreto en el repo.
- [ ] CORS, cookies y Redirect URI de producción verificados.
- [ ] Logs y healthcheck operativos.
- [ ] Smoke tests pasados y documentados.