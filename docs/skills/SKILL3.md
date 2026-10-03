---
name: spotify-integration
description: Integra Spotify en MigMusic (OAuth Authorization Code + PKCE, tokens, scopes, Web API, Web Playback SDK, errores, sesiones, variables de entorno) manteniendo los secretos en el backend Python y tratando Spotify como fuente separada de la música local. Úsala tras confirmar SPOTIFY-*.
---

# Skill: spotify-integration

## Responsabilidad única

Todo lo relativo a **Spotify**: autenticación, sesión, consumo de la Web API desde el backend Python y reproducción con el Web Playback SDK en el frontend. No trata audio local (`local-audio`) ni la lista (`doubly-linked-list`).

## Precondiciones (AGEND.md)

`SPOTIFY-001`…`SPOTIFY-005` `CONFIRMED`; `SPOTIFY-006` (funciones) para definir scopes; `DEPLOY-001/002` para Redirect URI y CORS; `backend-architecture-python` aplicado.

## ⚠️ Verificación obligatoria de documentación vigente

Las políticas, cuotas, endpoints disponibles y reglas de Redirect URI de Spotify **cambian**. Antes de codificar, el agente debe consultar la documentación oficial (developer.spotify.com) y registrar en un ADR:
- Reglas actuales de **Redirect URI** (HTTPS obligatorio, excepciones para loopback, `localhost` vs IP).
- Flujos de autorización permitidos (Authorization Code con PKCE; **no usar Implicit Grant**).
- **Modo desarrollo vs. cuota extendida:** límites de usuarios y de apps nuevas.
- **Endpoints restringidos o deprecados** para apps nuevas.
- **Requisitos del Web Playback SDK:** cuenta **Premium**, navegadores y **dispositivos móviles soportados** (históricamente limitado en móviles).
Si algo contradice lo que dice este documento, **manda la documentación oficial**; registrarlo y volver a `requirements-interview` si cambia el alcance.

## Arquitectura (capas)

```
domain/ports/music_provider.py        # MusicProvider (ABC): search(), get_track(), ...
domain/ports/token_store.py           # TokenStore (ABC): save/get/delete por sesión
application/services/spotify_auth_service.py   # inicia login, procesa callback, refresh, logout
infrastructure/spotify/spotify_oauth.py         # PKCE, state, intercambio de código, refresh
infrastructure/spotify/spotify_client.py        # HTTP a Web API (timeouts, reintentos, 401/429)
infrastructure/spotify/spotify_music_provider.py # implementa MusicProvider (mapea a Song)
infrastructure/security/session_token_store.py  # almacén de tokens ligado a sesión
api/routers/auth.py, spotify.py                 # endpoints delgados
frontend/players/SpotifyPlayer.ts               # implementa AudioPlayer con el SDK
```

Todas son clases con una responsabilidad; el cliente HTTP y el proveedor se inyectan (fácil de simular en pruebas).

## Flujo OAuth (Authorization Code + PKCE)

1. `GET /auth/spotify/login`: el backend genera `state` (aleatorio, ligado a la sesión) y `code_verifier`/`code_challenge` (PKCE), guarda ambos en la sesión y redirige a `accounts.spotify.com/authorize` con `client_id`, `redirect_uri`, `scope`, `state`, `code_challenge`.
2. Spotify redirige a `GET /auth/spotify/callback?code=…&state=…`.
3. El backend **valida `state`** (anti-CSRF), intercambia `code` por tokens en `accounts.spotify.com/api/token` usando `code_verifier` (y el **Client Secret solo aquí, en backend**, si el flujo/app lo requiere).
4. Guarda `access_token`, `refresh_token`, `expires_at` en el `TokenStore` (asociado a la sesión); **nunca** en `localStorage`.
5. Establece cookie de sesión: `HttpOnly`, `Secure` (en producción), `SameSite` acorde a `DEPLOY-002` (`Lax` si mismo sitio; `None; Secure` si dominios distintos), con `Path` y expiración razonables.
6. Redirige al frontend.

### Tokens y expiración
- El access token dura poco (~1 h): el backend lo **refresca automáticamente** antes de que expire o al recibir 401 (una sola vez, con bloqueo para evitar refrescos concurrentes).
- Si el refresh falla (revocado) → cerrar sesión de Spotify y pedir reconectar con un mensaje claro en la UI.
- Endpoint `GET /auth/spotify/token` para el SDK: devuelve un access token **vigente** al frontend autenticado (el SDK necesita un token para `getOAuthToken`); no devolver nunca el refresh token ni el Client Secret. Limitar por sesión y con `Cache-Control: no-store`.
- `POST /auth/spotify/logout`: borra tokens y sesión.

### Scopes (mínimo privilegio; ajustar según `SPOTIFY-006`)
Base típica para el SDK: `streaming`, `user-read-email`, `user-read-private`. Control/lectura de reproducción: `user-read-playback-state`, `user-modify-playback-state`. Solo si se aprueban: `playlist-read-private`, `user-library-read`, etc. Documentar cada scope y su motivo en el ADR.

## Variables de entorno

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=          # solo backend
SPOTIFY_REDIRECT_URI=           # idéntica a la registrada en el Dashboard
SESSION_SECRET_KEY=             # firma de cookies
FRONTEND_ORIGIN=                # para CORS
```
- `.env` fuera de git; `.env.example` sin valores.
- `Settings` valida su presencia al arrancar. Nunca imprimir su valor en logs.
- El **Client ID** no es secreto pero se lee de configuración igualmente.

## Web API (backend)

- Búsqueda de pistas, detalle de pista, (opcional) playlists/biblioteca del usuario según `SPOTIFY-006`.
- Mapeo a `Song` (`source = SPOTIFY`, `external_id` = URI `spotify:track:…`, título, artista, álbum, duración, portada).
- Timeouts, reintentos con backoff y **respeto de `Retry-After` en 429**.
- Paginación controlada; caché corta opcional de búsquedas.
- Errores mapeados a excepciones propias (`SpotifyAuthError`, `SpotifyRateLimitError`, `SpotifyApiError`) y luego a HTTP en `error_handlers.py`.

## Web Playback SDK (frontend)

- Cargar el script oficial del SDK dinámicamente dentro de `SpotifyPlayer`; crear `Spotify.Player` con `getOAuthToken` que pide un token fresco al backend.
- Al evento `ready` obtener `device_id`; para reproducir una pista se llama a la Web API **`PUT /me/player/play`** con `device_id` y `uris:[…]` (vía backend proxy o directo con token, según decisión de seguridad).
- `SpotifyPlayer implements AudioPlayer`: `play/pause/next/previous/seek/setVolume` mapeados a métodos del SDK (`resume`, `pause`, `seek`, `setVolume`, etc.).
- **Skip N segundos:** leer posición actual (`getCurrentState().position`) ± N ms y `seek()`, con límites [0, duración].
- Escuchar `player_state_changed` para sincronizar UI y detectar fin de pista → `moveNext()` de la lista.
- Errores del SDK: `initialization_error`, `authentication_error`, `account_error` (no Premium), `playback_error`; cada uno con un mensaje UX y acción (reconectar, informar Premium, reintentar).
- `not_ready`/desconexión: intentar reconectar y avisar.
- Autoplay: los navegadores exigen gesto del usuario; usar `player.activateElement()` cuando corresponda en el primer clic.
- Limitaciones a comunicar en la UI: sin control de velocidad, sin acceso al audio para visualizador/ecualizador real, sin gapless entre fuentes distintas.

## Separación de fuentes (regla dura)

- El SDK **solo** reproduce contenido Spotify. **Nunca** intentar meter un archivo local en el SDK.
- `Song.source` decide qué `AudioPlayer` usa la app (Strategy/Factory). Al cambiar de fuente entre canciones consecutivas: pausar/desactivar el player anterior antes de iniciar el siguiente.

## Seguridad

- Client Secret y refresh token **solo backend**.
- Validar `state`; PKCE; cookies `HttpOnly`.
- CORS con origen explícito y `allow_credentials` solo si hace falta.
- CSP compatible con el script del SDK y `sdk.scdn.co`.
- Rate limiting en `/auth/*`.
- No registrar tokens en logs; ofuscar en trazas.

## Pruebas

- **Unitarias:** `SpotifyOAuth` (generación PKCE/state, construcción de URLs, parseo de respuestas), `SpotifyAuthService` (refresh, expiración), `SpotifyMusicProvider` (mapeo) con un cliente HTTP simulado.
- **Integración:** rutas `/auth/*` y `/spotify/*` con doble de Spotify (`respx`/`httpx.MockTransport`, `responses`, etc.).
- **Manual guiado (Premium):** login, reproducir, pausar, seek, skip N seg, refresh de token tras > 1 h, logout, error de cuenta sin Premium.
- Nunca llamar a Spotify real en CI.

## Definición de terminado

- [ ] Login/logout/refresh funcionando con PKCE y `state`.
- [ ] Ningún secreto en repo ni en frontend.
- [ ] Reproducción, pausa, seek, skip ± N s y siguiente/anterior con Spotify (cuenta Premium).
- [ ] Errores del SDK y de la API con mensajes de usuario y logs sin datos sensibles.
- [ ] ADR con hallazgos de la documentación vigente.
- [ ] Redirect URIs de local y producción verificadas.