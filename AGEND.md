# AGEND.md â€” MigMusic

> **Fuente de verdad del proyecto MigMusic.**
> Este archivo es leÃ­do por el **agente de desarrollo**. No es documentaciÃ³n pasiva: es una guÃ­a operativa.
> El agente de desarrollo **debe entrevistar al usuario** (secciÃ³n [Requirements Interview](#requirements-interview)), registrar las respuestas aquÃ­ mismo, y solo cuando se cumpla el [Implementation Gate](#implementation-gate) comenzar a programar.

- **Idioma de conversaciÃ³n con el usuario:** espaÃ±ol.
- **Idioma del cÃ³digo:** inglÃ©s (ver [Restricciones globales](#restricciones-globales)).
- **Propietario del proyecto:** Miguel.
- **VersiÃ³n del documento:** 1.2.0 (entrevista F0 completada y gate aprobado el 2026-09-28).

---

## 0. CÃ³mo debe usar este archivo el agente de desarrollo

Orden obligatorio de lectura y actuaciÃ³n:

1. Leer este archivo completo, de arriba abajo.
2. Leer las skills listadas en [Ãndice de skills](#Ã­ndice-de-skills). Empezar por `requirements-interview`, que gobierna la entrevista.
3. Ejecutar la entrevista **progresiva** (rondas de 4â€“6 preguntas, nunca todo de golpe).
4. Tras cada respuesta del usuario, **editar este archivo**: cambiar `Status`, rellenar `Answer` y `DecidedOn`, y aÃ±adir una lÃ­nea al [Decision Log](#decision-log).
5. Cuando el [Implementation Gate](#implementation-gate) estÃ© verde, implementar siguiendo el [Roadmap](#roadmap) y las skills tÃ©cnicas.
6. Ante cualquier cambio de alcance posterior, volver a este archivo, actualizarlo y **solo entonces** cambiar el cÃ³digo.

Regla de oro: **si algo no estÃ¡ `CONFIRMED` aquÃ­, el agente no lo asume.** Puede recomendarlo, pero debe preguntarlo.

---

## 1. Contexto del proyecto

**MigMusic** es un reproductor de mÃºsica web completo. NaciÃ³ como un **taller acadÃ©mico de estructuras de datos** cuyo nÃºcleo es la **lista doblemente enlazada** aplicada a una lista de reproducciÃ³n de canciones. El objetivo es convertir ese ejercicio en un producto real: con reproductor funcional, mÃºsica de Spotify, mÃºsica local del equipo del usuario, interfaz moderna y animada, diseÃ±o responsive y despliegue en la nube.

Dos dimensiones conviven y ambas son evaluables:

| DimensiÃ³n | QuÃ© debe demostrar |
|---|---|
| **AcadÃ©mica** | Una lista doblemente enlazada **real** (nodos con `previous`/`next`), no un array disfrazado, explicable paso a paso. |
| **Producto** | Un reproductor web usable, bonito, seguro, probado y desplegado. |

## 2. Requisitos originales del taller (inmutables)

El taller solicita construir una aplicaciÃ³n usando el concepto de **LISTA DOBLEMENTE ENLAZADA** para simular y gestionar una lista de reproducciÃ³n:

- [ ] Agregar una canciÃ³n al inicio.
- [ ] Agregar una canciÃ³n al final.
- [ ] Agregar una canciÃ³n en cualquier posiciÃ³n.
- [ ] Eliminar una canciÃ³n.
- [ ] Adelantar canciÃ³n (siguiente).
- [ ] Retroceder canciÃ³n (anterior).
- [ ] Interfaz frontend con la que el usuario interactÃºe.
- [ ] Otras funcionalidades adicionales pertinentes (mÃ­nimo 2, propuestas por el agente y elegidas por el usuario â€” ver `FEAT-*`).

> Estos requisitos **no pueden eliminarse ni degradarse** por ninguna decisiÃ³n posterior.

## 3. Objetivo de MigMusic

Debe tener: reproductor funcional Â· playlist funcional Â· lista doblemente enlazada Â· mÃºsica de Spotify Â· mÃºsica local Â· interfaz moderna Â· animaciones Â· diseÃ±o responsive Â· controles de reproducciÃ³n Â· adelantar segundos Â· retroceder segundos Â· agregar canciones Â· eliminar canciones Â· navegar entre canciones Â· despliegue en la nube.

## 4. Requisitos funcionales (RF)

| ID | Requisito | Origen |
|---|---|---|
| RF-01 | Play / Pause | Producto |
| RF-02 | Next / Previous (navegaciÃ³n por la lista doblemente enlazada) | Taller |
| RF-03 | **Skip forward N segundos** (N definido en `PLAYER-001`) | Producto |
| RF-04 | **Skip backward N segundos** (N definido en `PLAYER-002`) | Producto |
| RF-05 | Seek mediante barra de progreso | Producto |
| RF-06 | Volume y Mute | Producto |
| RF-07 | Agregar canciÃ³n al inicio / al final / en posiciÃ³n arbitraria | Taller |
| RF-08 | Eliminar canciÃ³n (por referencia y por posiciÃ³n) | Taller |
| RF-09 | Seleccionar canciÃ³n de la lista y reproducirla | Producto |
| RF-10 | Fuente **Spotify** (Web API + Web Playback SDK) | Producto |
| RF-11 | Fuente **MÃºsica local** (File Picker, HTML5 Audio o alternativa adecuada) | Producto |
| RF-12 | Playlist unificada que puede contener canciones de ambas fuentes, respetando sus lÃ­mites tÃ©cnicos | Producto |
| RF-13 | â‰¥ 2 funcionalidades adicionales aprobadas por el usuario | Taller |
| RF-14 | Interfaz **funcional**, no mockup: todos los controles principales operan de verdad | Producto |

## 5. Requisitos no funcionales (RNF)

| ID | Requisito |
|---|---|
| RNF-01 | **POO** en todo el sistema (backend Python y frontend). Ver [Arquitectura](#8-arquitectura-objetivo). |
| RNF-02 | Estructura de carpetas **bien organizada y separada por capas/responsabilidades**, de modo que se note buena arquitectura. |
| RNF-03 | Backend **100 % Python**. Ninguna lÃ³gica de servidor en otro lenguaje. |
| RNF-04 | CÃ³digo, comentarios tÃ©cnicos, nombres y tipos **en inglÃ©s**. |
| RNF-05 | Responsive: desktop, laptop, tablet y mobile. |
| RNF-06 | Animaciones acordes al nivel decidido (`VIS-006`), respetando `prefers-reduced-motion`. |
| RNF-07 | Seguridad: secretos solo en variables de entorno; OAuth correcto; sin secretos en el frontend. |
| RNF-08 | Testing automatizado (unitario, integraciÃ³n, e2e mÃ­nimo). |
| RNF-09 | Desplegable en la nube con HTTPS, CORS, logs y configuraciÃ³n de producciÃ³n. |
| RNF-10 | Accesibilidad bÃ¡sica (teclado, foco visible, ARIA en controles, contraste). |

## Restricciones globales

1. **Backend: Python obligatorio.** El framework (FastAPI / Flask / Django) se decide en `BACK-001`.
2. **ProgramaciÃ³n Orientada a Objetos** obligatoria: clases con responsabilidad Ãºnica, encapsulaciÃ³n, abstracciÃ³n mediante interfaces/clases abstractas, polimorfismo entre fuentes de audio, composiciÃ³n sobre herencia, inyecciÃ³n de dependencias.
3. **CÃ³digo en inglÃ©s**: variables, funciones, clases, interfaces, tipos, componentes, mÃ©todos y comentarios tÃ©cnicos.
4. **La lista doblemente enlazada no puede sustituirse por un array/list nativo** como estructura de la playlist activa.
5. **Spotify y mÃºsica local son dos fuentes distintas.** El Web Playback SDK **no** reproduce archivos locales. Ver skill `spotify-integration` y `local-audio`.
6. **NingÃºn secreto** (Client Secret, tokens, claves) en el repositorio ni en el bundle del frontend.
7. **Estructura organizada y separada** (ver secciÃ³n 8): cada capa en su carpeta, sin dependencias circulares, sin lÃ³gica de negocio en controladores/rutas ni en componentes de UI.

---

## 8. Arquitectura objetivo

> Esta arquitectura es la **hipÃ³tesis de trabajo** que el agente debe evaluar y ajustar con el usuario (`ARCH-*`, `BACK-*`, `FRONT-*`). Los principios (capas, POO, separaciÃ³n) **no son negociables**; los detalles sÃ­.

### 8.1 Principios

- **Arquitectura por capas / hexagonal (ports & adapters):** el dominio no conoce frameworks, HTTP, Spotify ni base de datos.
- **Dependencias hacia adentro:** `api â†’ application â†’ domain`; `infrastructure â†’ domain` (implementa puertos definidos en dominio/aplicaciÃ³n).
- **SOLID** aplicado explÃ­citamente (y demostrable en revisiÃ³n de cÃ³digo).
- **InyecciÃ³n de dependencias** en el punto de composiciÃ³n (`container`/`main`), nunca `import` de implementaciones concretas dentro del dominio.
- **DTOs/Schemas** en el borde (API); las entidades de dominio nunca se serializan directamente.
- **Excepciones de dominio propias**, traducidas a respuestas HTTP en un Ãºnico lugar.

### 8.2 Estructura de carpetas propuesta (monorepo)

```
migmusic/
â”œâ”€â”€ AGEND.md
â”œâ”€â”€ README.md
â”œâ”€â”€ .env.example                      # solo nombres de variables, jamÃ¡s valores reales
â”œâ”€â”€ docker-compose.yml                # entorno local reproducible
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ architecture.md               # diagramas y decisiones (ADR)
â”‚   â”œâ”€â”€ adr/                          # Architecture Decision Records (uno por decisiÃ³n)
â”‚   â”œâ”€â”€ api.md
â”‚   â””â”€â”€ testing.md                    # estrategia de pruebas + reporte criterio â†’ evidencia (F11)
â”œâ”€â”€ docs/skills/                           # skills para el agente (entregadas junto a este archivo)
â”œâ”€â”€ backend/                          # 100 % Python
â”‚   â”œâ”€â”€ pyproject.toml
â”‚   â”œâ”€â”€ src/migmusic/
â”‚   â”‚   â”œâ”€â”€ main.py                   # composition root: crea app y cablea dependencias
â”‚   â”‚   â”œâ”€â”€ core/                     # transversal: config, logging, errores base, seguridad
â”‚   â”‚   â”‚   â”œâ”€â”€ config.py             # Settings (lee variables de entorno)
â”‚   â”‚   â”‚   â”œâ”€â”€ logging.py
â”‚   â”‚   â”‚   â””â”€â”€ exceptions.py
â”‚   â”‚   â”œâ”€â”€ domain/                   # REGLAS DE NEGOCIO PURAS (sin frameworks)
â”‚   â”‚   â”‚   â”œâ”€â”€ entities/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ song.py           # Song (value object / entity)
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ playlist.py       # Playlist (usa DoublyLinkedList)
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ audio_source.py   # enum AudioSourceType {LOCAL, SPOTIFY}
â”‚   â”‚   â”‚   â”œâ”€â”€ structures/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ node.py           # Node
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ doubly_linked_list.py  # DoublyLinkedList
â”‚   â”‚   â”‚   â”œâ”€â”€ ports/                # interfaces abstractas (ABC / Protocol)
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ playlist_repository.py
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ music_provider.py # contrato comÃºn para fuentes de mÃºsica
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ token_store.py
â”‚   â”‚   â”‚   â””â”€â”€ exceptions.py         # EmptyPlaylistError, InvalidPositionError...
â”‚   â”‚   â”œâ”€â”€ application/              # CASOS DE USO (orquestan dominio + puertos)
â”‚   â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ playlist_service.py
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ playback_service.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ spotify_auth_service.py
â”‚   â”‚   â”‚   â””â”€â”€ dto/
â”‚   â”‚   â”œâ”€â”€ infrastructure/          # ADAPTADORES concretos
â”‚   â”‚   â”‚   â”œâ”€â”€ spotify/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ spotify_client.py       # cliente HTTP a Spotify Web API
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ spotify_oauth.py        # Authorization Code + PKCE, refresh
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ spotify_music_provider.py  # implementa MusicProvider
â”‚   â”‚   â”‚   â”œâ”€â”€ persistence/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ in_memory_playlist_repository.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sql_playlist_repository.py   # solo si se aprueba DB
â”‚   â”‚   â”‚   â””â”€â”€ security/
â”‚   â”‚   â”‚       â””â”€â”€ session_token_store.py
â”‚   â”‚   â””â”€â”€ api/                      # CAPA DE ENTRADA (HTTP)
â”‚   â”‚       â”œâ”€â”€ routers/              # controladores delgados: sin lÃ³gica de negocio
â”‚   â”‚       â”œâ”€â”€ schemas/              # request/response models
â”‚   â”‚       â”œâ”€â”€ dependencies.py       # inyecciÃ³n de dependencias del framework
â”‚   â”‚       â””â”€â”€ error_handlers.py     # excepciones de dominio â†’ HTTP
â”‚   â””â”€â”€ tests/
â”‚       â”œâ”€â”€ unit/                     # dominio y servicios (sin red, sin disco)
â”‚       â”œâ”€â”€ integration/              # API + adaptadores (con dobles de Spotify)
â”‚       â””â”€â”€ conftest.py
â”œâ”€â”€ frontend/                         # tecnologÃ­a segÃºn FRONT-001
â”‚   â”œâ”€â”€ package.json
â”‚   â”œâ”€â”€ vercel.json                   # rewrite /api/* â†’ Render (DEPLOY-002, un solo origen)
â”‚   â””â”€â”€ src/
â”‚       â”œâ”€â”€ domain/                   # DoublyLinkedList (espejo, si se aprueba ARCH-001), Song, tipos
â”‚       â”œâ”€â”€ players/                  # POO: AudioPlayer (abstracto), LocalAudioPlayer, SpotifyPlayer
â”‚       â”œâ”€â”€ services/                 # ApiClient, PlaylistController, PlaybackController
â”‚       â”œâ”€â”€ storage/                  # LocalLibraryRepository (IndexedDB) si se aprueba
â”‚       â”œâ”€â”€ ui/
â”‚       â”‚   â”œâ”€â”€ components/           # presentacionales, sin lÃ³gica de negocio
â”‚       â”‚   â”œâ”€â”€ layouts/
â”‚       â”‚   â””â”€â”€ animations/
â”‚       â”œâ”€â”€ styles/                   # design tokens (colores, espaciado, motion)
â”‚       â””â”€â”€ main.*
â””â”€â”€ render.yaml                       # IaC: blueprint de Render (DEPLOY-001)
```

### 8.3 Clases centrales (nombres de referencia)

| Clase | Capa | Responsabilidad Ãºnica |
|---|---|---|
| `Node` | domain | Contener `song`, `previous`, `next`. |
| `DoublyLinkedList` | domain | Operaciones estructurales de la lista y puntero `current`. |
| `Song` | domain | Datos inmutables de una canciÃ³n y su `AudioSourceType`. |
| `Playlist` | domain | Nombre + `DoublyLinkedList`; reglas propias (duplicados, modos repeat/shuffle si se aprueban). |
| `MusicProvider` (ABC) | domain/ports | Contrato de una fuente de mÃºsica (bÃºsqueda, resoluciÃ³n de reproducciÃ³n). |
| `SpotifyMusicProvider` | infrastructure | Implementa `MusicProvider` con Spotify Web API. |
| `PlaylistRepository` (ABC) | domain/ports | Persistir/recuperar playlists. |
| `PlaylistService` | application | Casos de uso: crear, aÃ±adir, insertar, eliminar, mover. |
| `PlaybackService` | application | Casos de uso: next, previous, seek, skip N segundos (estado de reproducciÃ³n). |
| `SpotifyAuthService` | application | Flujo OAuth, refresh de tokens, cierre de sesiÃ³n. |
| `AudioPlayer` (abstracta, frontend) | frontend/players | `play/pause/seek/setVolume/onEnded...` |
| `LocalAudioPlayer` / `SpotifyPlayer` | frontend/players | Polimorfismo: misma interfaz, distinto motor. |

### 8.4 Patrones esperados (justificar en ADR si se cambian)

Strategy (fuentes de audio) Â· Repository (persistencia) Â· Factory (creaciÃ³n de players/providers) Â· Adapter (Spotify) Â· Observer/Event emitter (estado del player â†’ UI) Â· Dependency Injection (composition root).

### 8.5 DÃ³nde vive la lista doblemente enlazada (decisiÃ³n crÃ­tica â†’ `ARCH-001`)

El reproductor de mÃºsica local corre **en el navegador**; los archivos locales no deben viajar al servidor salvo decisiÃ³n explÃ­cita. El backend es Python. Hay tensiÃ³n que el agente debe resolver con el usuario:

- **OpciÃ³n A â€” DLL solo en backend (Python):** mÃ¡xima pureza acadÃ©mica en Python, pero cada Next/Previous implica red; incÃ³modo con archivos locales.
- **OpciÃ³n B â€” DLL solo en frontend:** respuesta inmediata, pero el backend Python queda reducido a OAuth/persistencia y pierde peso acadÃ©mico.
- **OpciÃ³n C â€” DLL en ambos con contrato compartido (recomendada como hipÃ³tesis):** el backend Python es la fuente de verdad de playlists persistidas y expone la API; el frontend mantiene una implementaciÃ³n equivalente para navegaciÃ³n instantÃ¡nea; ambas se validan con **los mismos casos de prueba (fixtures de contrato)**. Costo: duplicaciÃ³n controlada y disciplina de sincronizaciÃ³n.

El agente debe explicar esto, recomendar y **preguntar**; no asumir.

---

## 9. Lista doblemente enlazada â€” especificaciÃ³n

Estructura mÃ­nima:

```
Node
- song
- previous
- next

DoublyLinkedList
- head
- tail
- current
- size
```

Operaciones mÃ­nimas (nombres en inglÃ©s; adaptar al estilo del lenguaje, ej. `snake_case` en Python):

`insertAtBeginning()` Â· `insertAtEnd()` Â· `insertAt()` Â· `remove()` Â· `removeAt()` Â· `find()` Â· `moveNext()` Â· `movePrevious()` Â· `getCurrent()` Â· `getSize()` Â· `clear()`

Reglas:

- ImplementaciÃ³n **real** con nodos enlazados. Prohibido usar `list`/`Array` como almacenamiento interno de la estructura.
- Mantener invariantes: `head.previous is None`, `tail.next is None`, `size` coherente, `current` vÃ¡lido o `None`.
- Casos borde obligatorios: lista vacÃ­a, un solo elemento, inserciÃ³n/eliminaciÃ³n en extremos, posiciÃ³n fuera de rango, eliminar el nodo `current`, `moveNext` en `tail`, `movePrevious` en `head`.
- DecisiÃ³n pendiente: comportamiento en extremos (Â¿se detiene o es circular?) â†’ `PLAYLIST-009`.
- El agente debe poder **explicar al usuario cÃ³mo la lista se usa dentro de la playlist** (skill `doubly-linked-list` incluye guion de explicaciÃ³n).
- Complejidad documentada por operaciÃ³n (ej. `insertAtBeginning` O(1), `insertAt` O(n)).

## 10. Spotify

MigMusic usa **Spotify Web API** y **Spotify Web Playback SDK**. Debe documentarse y respetarse:

- **OAuth** con *Authorization Code Flow* (con PKCE cuando el cliente lo requiera). No usar Implicit Grant (obsoleto).
- **Tokens:** access token de vida corta + refresh token; **el Client Secret jamÃ¡s sale del backend**.
- **Scopes** mÃ­nimos necesarios (el agente los lista y justifica en `SPOTIFY-*`).
- **Redirect URI:** debe coincidir exactamente con la registrada en el Spotify Dashboard; las reglas de HTTPS/loopback **deben verificarse en la documentaciÃ³n vigente** antes de configurar.
- **Client ID / Client Secret / variables de entorno:** solo por `.env` local (ignorado por git) y variables del proveedor cloud.
- **Requisitos de cuenta:** el Web Playback SDK exige cuenta **Spotify Premium**; verificar limitaciones actuales de modo desarrollo (usuarios permitidos, cuotas) y de navegadores/mÃ³viles soportados.
- **Manejo de errores:** 401 (token expirado â†’ refresh), 403, 429 (respetar `Retry-After`), errores del SDK (`initialization_error`, `authentication_error`, `account_error`, `playback_error`).
- **Sesiones y expiraciÃ³n:** cookie de sesiÃ³n `HttpOnly`, `Secure`, `SameSite` adecuada; refresh transparente.
- **SeparaciÃ³n de fuentes:** el SDK reproduce solo contenido de Spotify. **Nunca** intentar reproducir archivos locales con Ã©l.

> El agente **debe consultar la documentaciÃ³n oficial vigente de Spotify** antes de implementar (las polÃ­ticas de acceso y endpoints cambian con el tiempo) y registrar en un ADR cualquier limitaciÃ³n encontrada.

Detalle operativo: skill `spotify-integration`.

## 11. MÃºsica local

- SelecciÃ³n con **File Picker**; **drag and drop** si se aprueba (`LOCAL-003`).
- Formatos: MP3, WAV y otros compatibles con el navegador (lista final en `LOCAL-001`; el agente debe advertir diferencias de soporte entre navegadores).
- ReproducciÃ³n con **HTML5 Audio API** (o alternativa tÃ©cnicamente adecuada, ej. Web Audio API si se aprueba visualizador/ecualizador).
- Debe poder: reproducir, pausar, avanzar, retroceder, seek, cambiar canciÃ³n, eliminar canciÃ³n.
- Persistencia tras cerrar el navegador: implica almacenar blobs (IndexedDB) o solo metadatos con re-selecciÃ³n de archivos â†’ **explicar implicaciones** (`LOCAL-006`, `LOCAL-008`).
- GestiÃ³n de memoria: liberar `URL.createObjectURL` con `revokeObjectURL`.
- Privacidad: por defecto, los archivos locales **no se suben** al servidor.

Detalle operativo: skill `local-audio`.

## 12. Seguridad

- Secretos solo en variables de entorno; `.env` en `.gitignore`; `.env.example` sin valores.
- Client Secret y refresh tokens solo en backend; sesiÃ³n por cookie `HttpOnly`.
- Validar `state` en OAuth (anti-CSRF) y usar PKCE.
- CORS restrictivo (orÃ­genes explÃ­citos, nunca `*` con credenciales).
- ValidaciÃ³n de entrada con schemas; lÃ­mites de tamaÃ±o y tipo para cualquier subida.
- Cabeceras de seguridad (CSP compatible con el SDK de Spotify, HSTS en producciÃ³n).
- Dependencias fijadas y auditadas; logs **sin** tokens ni datos sensibles.
- Rate limiting bÃ¡sico en endpoints de autenticaciÃ³n.

## 13. Testing

- **Unit (obligatorio, alta cobertura en dominio):** `DoublyLinkedList`, `Playlist`, servicios.
- **IntegraciÃ³n:** rutas API con dobles de Spotify (sin llamar a Spotify real en CI).
- **Contrato DLL:** mismos casos en Python y en frontend si aplica `ARCH-001 = C`.
- **Frontend:** pruebas de componentes/controladores y de los players con dobles.
- **E2E mÃ­nimo:** flujo agregar â†’ reproducir â†’ next â†’ previous â†’ skip N seg â†’ eliminar.
- **Manual guiado:** checklist responsive y Spotify real (requiere cuenta Premium).
- Herramientas concretas: `TEST-001`.

Detalle operativo: skill `testing-quality`.

## 14. Despliegue

Debe contemplarse: frontend, backend, HTTPS, variables de entorno, Spotify OAuth, CORS, Redirect URI de producciÃ³n, logs y configuraciÃ³n de producciÃ³n. Plataforma y topologÃ­a: `DEPLOY-*`. Detalle operativo: skill `deployment-cloud`.

---

## Ãndice de skills

UbicaciÃ³n: carpeta `docs/skills/SKILL*.md`. Cada una tiene **una responsabilidad concreta**.

| Skill | Responsabilidad | CuÃ¡ndo se activa |
|---|---|---|
| `requirements-interview` | Conducir la entrevista progresiva, registrar respuestas, controlar el gate. | **Siempre primero.** |
| `backend-architecture-python` | Estructura por capas, POO, SOLID y reglas de organizaciÃ³n del backend Python. | Al iniciar implementaciÃ³n backend y en cada revisiÃ³n. |
| `doubly-linked-list` | Implementar, probar y explicar la lista doblemente enlazada. | Al implementar la playlist. |
| `spotify-integration` | OAuth, tokens, Web API, Web Playback SDK, errores. | Tras `SPOTIFY-*` confirmadas. |
| `local-audio` | Audio local, metadata, persistencia, formatos. | Tras `LOCAL-*` confirmadas. |
| `ui-ux-design` | DiseÃ±o visual, animaciones, responsive, accesibilidad, frontend POO. | Tras `VIS-*`, `UX-*`, `FRONT-*` confirmadas. |
| `testing-quality` | Estrategia y ejecuciÃ³n de pruebas, criterios de calidad. | Continuamente y antes de cada entrega. |
| `deployment-cloud` | Despliegue, HTTPS, CORS, entornos, logs. | Tras `DEPLOY-*` confirmadas. |

---

## Sistema de estados

| Estado | Significado | AcciÃ³n del agente |
|---|---|---|
| `PENDING` | AÃºn no preguntada o sin respuesta. | Preguntar (cuando le toque por orden y dependencias). |
| `PROPOSED` | El agente propuso una opciÃ³n/recomendaciÃ³n y espera confirmaciÃ³n. | No implementar; pedir confirmaciÃ³n. |
| `CONFIRMED` | El usuario decidiÃ³; respuesta registrada. | Usar como requisito firme. No volver a preguntar. |
| `REJECTED` | El usuario descartÃ³ la opciÃ³n/funcionalidad. | No implementar; no volver a proponer salvo que el usuario lo pida. |

Transiciones vÃ¡lidas: `PENDING â†’ PROPOSED â†’ CONFIRMED | REJECTED`, `PENDING â†’ CONFIRMED | REJECTED`, y `CONFIRMED â†’ PENDING` Ãºnicamente si el usuario quiere **reabrir** la decisiÃ³n (registrar en Decision Log).

Cada pregunta tiene: `Status`, `Priority` (`CRITICAL` bloquea el gate / `NORMAL` no), `DependsOn`, `Question`, `Guidance` (quÃ© explicar/alternativas), `FollowUps` (preguntas adicionales condicionales), `Answer`, `DecidedOn`.

Al confirmar, el agente escribe por ejemplo:

```yaml
VIS-001:
  Status: CONFIRMED
  Answer: "Glassmorphism oscuro con acentos neÃ³n"
  DecidedOn: 2026-10-01
```

---

## Requirements Interview

### Reglas de la entrevista (resumen; el detalle estÃ¡ en la skill `requirements-interview`)

1. **Progresiva:** rondas temÃ¡ticas de **4â€“6 preguntas**. Anunciar la ronda ("Vamos a definir el diseÃ±o visual de MigMusic."), preguntar, esperar respuesta, registrar, y pasar a la siguiente.
2. **Nunca** preguntar todo de una vez ni repetir preguntas `CONFIRMED`/`REJECTED`.
3. Respetar `DependsOn`: no preguntar una pregunta si sus dependencias siguen `PENDING`, salvo dependencia tÃ©cnica que justifique alterar el orden (explicarlo).
4. Si una respuesta abre una decisiÃ³n nueva, **crear** la pregunta adicional (ID nuevo con sufijo, ej. `LOCAL-006a`) en `PENDING` y hacerla en la misma ronda o la siguiente.
5. Para decisiones tÃ©cnicas: explicar opciones, ventajas/desventajas, **recomendar**, preguntar y registrar. No asumir.
6. Si el usuario dice "no sÃ© / lo que recomiendes": pasar a `PROPOSED` con la recomendaciÃ³n, pedir un "sÃ­" explÃ­cito y entonces `CONFIRMED`.
7. Usar lenguaje claro; el usuario tiene interÃ©s en computaciÃ³n y redes y prefiere explicaciones **profundas y conceptuales**: cuando una decisiÃ³n tenga consecuencias tÃ©cnicas, explicar el porquÃ©, no solo el quÃ©.

### Orden recomendado de rondas

| Ronda | Tema | Prefijo | Depende de |
|---|---|---|---|
| R1 | Restricciones del proyecto | `CONS` | â€” |
| R2 | DiseÃ±o visual | `VIS` | R1 |
| R3 | UX | `UX` | R2 |
| R4 | Reproductor (core) | `PLAYER` | R1 |
| R5 | Playlist | `PLAYLIST` | R4 |
| R6 | MÃºsica local | `LOCAL` | R4, R5 |
| R7 | Spotify | `SPOTIFY` | R4, R5 |
| R8 | Frontend | `FRONT` | R2, R3, R6, R7 |
| R9 | Backend | `BACK` | R5, R7 |
| R10 | Base de datos | `DB` | R5, R6, R9 |
| R11 | Funcionalidades adicionales | `FEAT` | R4â€“R10 |
| R12 | Despliegue | `DEPLOY` | R8, R9, R10 |
| R13 | Testing | `TEST` | R8, R9 |

Transversal: `ARCH` (arquitectura) se plantea en **R5** y se afina en **R8â€“R9** porque depende de dÃ³nde vive la lista y de la persistencia.

**Dependencias tÃ©cnicas que autorizan alterar el orden (ejemplos):**
- `SPOTIFY-004` (entorno de despliegue/Redirect URI) depende de `DEPLOY-001`.
- `FRONT-001` (tecnologÃ­a) puede adelantarse si `VIS-*`/`FEAT-*` exigen capacidades concretas (ej. visualizador con Web Audio).
- `DB-001` depende de `LOCAL-006` (persistencia local) y `PLAYLIST-001` (mÃºltiples playlists).
- `FEAT-*` de Web Audio (ecualizador/visualizador) modifica `LOCAL-*` y `SPOTIFY-*` (el SDK **no** expone audio para anÃ¡lisis; explicarlo).

---

### R1 â€” Project Constraints Questions

```yaml
CONS-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: []
  Question: "Â¿Este proyecto se entrega y evalÃºa como trabajo acadÃ©mico (con sustentaciÃ³n de la lista doblemente enlazada) ademÃ¡s de ser un producto real? Â¿Hay fecha lÃ­mite?"
  Guidance: "Define el peso de la parte acadÃ©mica (documentaciÃ³n, explicabilidad) y el plazo, que condiciona el alcance del roadmap."
  Answer: "Trabajo acadÃ©mico + producto real. Fecha lÃ­mite: 2026-10-02"
  DecidedOn: 2026-09-28

CONS-001a:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "Con 4 dÃ­as hasta el 02/10, Â¿quÃ© nivel de alcance aceptas?"
  Guidance: "A: alcance completo recomendado. B: sin Spotify. C: todo el alcance con riesgo de no cerrar."
  Answer: "A - alcance completo recomendado; FEAT reducidas a 4 de bajo coste; sin visualizador/waveform/ecualizador/queue/velocidad/atajos"
  DecidedOn: 2026-09-28

CONS-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "Â¿TrabajarÃ¡s solo o en equipo? Â¿CuÃ¡l es tu nivel con Python, POO y el frontend que elijamos?"
  Guidance: "Ajusta la profundidad de explicaciones, comentarios y nivel de abstracciÃ³n."
  Answer: "Trabajo en solo. Nivel tÃ©cnico: ver CONS-002a"
  DecidedOn: 2026-09-28

CONS-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "Â¿QuÃ© entorno de desarrollo usas (sistema operativo, editor, versiÃ³n de Python/Node instaladas, Docker disponible)?"
  Guidance: "Determina scripts de arranque, Docker Compose y versiones mÃ­nimas."
  Answer: "Windows, VS Code, Python 3.11/3.13, Node 26, npm 11, Git 2.55, sin Docker"
  DecidedOn: 2026-09-28

CONS-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "Â¿Tienes o puedes crear una cuenta de Spotify Premium para probar el Web Playback SDK? Â¿QuiÃ©n mÃ¡s necesitarÃ¡ probar (usuarios de prueba)?"
  Guidance: "El SDK requiere Premium y el modo desarrollo de Spotify limita usuarios. Puede cambiar el alcance de la demo."
  Answer: "Cuenta Spotify Premium disponible"
  DecidedOn: 2026-09-28

CONS-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "Â¿Hay presupuesto para la nube (gratis Ãºnicamente, o puedes pagar algo)? Â¿Tienes dominio propio?"
  Guidance: "Condiciona la plataforma de despliegue y HTTPS."
  Answer: "Solo planes gratuitos en nube y herramientas"
  DecidedOn: 2026-09-28

CONS-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "Â¿QuÃ© idioma debe tener la interfaz de usuario de MigMusic (espaÃ±ol, inglÃ©s o ambos)?"
  Guidance: "El cÃ³digo va en inglÃ©s siempre; esto se refiere solo a los textos visibles. Si son ambos, planificar i18n."
  Answer: "Interfaz bilingÃ¼e: espaÃ±ol + inglÃ©s (i18n por diccionario de claves)"
  DecidedOn: 2026-09-28

CONS-002a:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [CONS-002]
  Question: "Â¿CuÃ¡l es tu nivel con Python, POO y frontend?"
  Guidance: "Ajusta profundidad de explicaciones y comentarios. Se pregunta en la fase de pulido (F9)."
  Answer: null
  DecidedOn: null
```

### R2 â€” Visual Design Questions

```yaml
VIS-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "Â¿QuÃ© estilo visual quieres para MigMusic? (moderno, futurista, minimalista, neÃ³n, glassmorphism, retro, oscuro tipo reproductor musical, otro)"
  Guidance: "Ofrecer 2â€“3 combinaciones concretas con una breve descripciÃ³n de cÃ³mo se verÃ­a cada una."
  Answer: "E - Espacio + bento grid (sustituye a \"D - Retro/vinilo\" de 2026-09-28; rediseÃ±o completo en VIS-013)"
  DecidedOn: 2026-10-02

VIS-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-001]
  Question: "Â¿Prefieres tema oscuro, claro o ambos (con selector)?"
  Guidance: "Ambos implica design tokens con dos paletas y mayor esfuerzo de pruebas de contraste."
  Answer: "Ambos temas con selector"
  DecidedOn: 2026-09-28

VIS-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-001]
  Question: "Â¿QuÃ© colores principales quieres?"
  Guidance: "Aceptar nombres, hex o una referencia (una app, una imagen). Validar contraste accesible."
  Answer: "Azul marino / elÃ©ctrico + negro; acentos a cargo del agente"
  DecidedOn: 2026-09-28

VIS-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-003]
  Question: "Â¿QuÃ© colores secundarios / de acento quieres?"
  Guidance: "Proponer una paleta derivada si no tiene preferencia."
  Answer: "Primario #1E6BFF, acento #4338CA, fondo #0A0D14 (opciÃ³n i, sobria)"
  DecidedOn: 2026-09-28

VIS-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-003]
  Question: "Â¿Quieres usar gradientes? Â¿Fijos o que cambien segÃºn la portada de la canciÃ³n?"
  Guidance: "Gradientes dinÃ¡micos por portada requieren extraer color dominante (costo tÃ©cnico moderado)."
  Answer: "Gradientes fijos (nebulosa y campo estelar del fondo espacial), nunca dinÃ¡micos por portada; levanta el rechazo \"Sin gradientes\" de 2026-09-28 (ver VIS-013)"
  DecidedOn: 2026-10-02

VIS-006:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-001]
  Question: "Â¿QuÃ© tan intensas quieres las animaciones: sutiles, moderadas o muy animadas?"
  Guidance: "Explicar impacto en rendimiento mÃ³vil y en accesibilidad (prefers-reduced-motion)."
  Answer: "Sutiles, respetando prefers-reduced-motion"
  DecidedOn: 2026-09-28

VIS-007:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "Â¿Quieres un visualizador de audio?"
  Guidance: "Con mÃºsica local es viable (Web Audio API AnalyserNode). Con Spotify SDK NO se puede analizar el audio: advertir. Puede simularse visualmente (no real) â€” explicar la diferencia honestamente."
  FollowUps: ["Si sÃ­: crear FEAT-* de visualizador y revisar LOCAL-* (Web Audio)."]
  Answer: "No aplica por CONS-001a (sin visualizador)"
  DecidedOn: 2026-09-28

VIS-008:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [VIS-007]
  Question: "Â¿Quieres ondas de audio (waveform) en la barra de progreso?"
  Guidance: "Waveform real requiere decodificar el archivo local; para Spotify no estÃ¡ disponible."
  Answer: "No aplica por CONS-001a (sin waveform)"
  DecidedOn: 2026-09-28

VIS-009:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "Â¿Quieres animaciones en la portada de la canciÃ³n (giro tipo vinilo, pulso, parallax)?"
  Guidance: "Mostrar opciones con una descripciÃ³n visual."
  Answer: "Solo microinteracciones sutiles en CSS puro: pulso suave en la portada al reproducir, sin giro tipo vinilo ni parallax"
  DecidedOn: 2026-09-28

VIS-010:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "Â¿Quieres efectos visuales cuando cambia la canciÃ³n (transiciÃ³n de portada, cambio de fondo, etc.)?"
  Guidance: "Vincular con VIS-005 si hay gradientes dinÃ¡micos."
  Answer: "Cross-fade de portada y titulo al cambiar de cancion, en CSS puro (transform/opacity)"
  DecidedOn: 2026-09-28

VIS-011:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "Â¿Quieres microinteracciones en botones y controles (hover, ripple, rebote al pulsar)?"
  Guidance: "Bajo costo, alto efecto percibido."
  Answer: "Si - hover, ripple y foco visibles en botones y controles, con prefers-reduced-motion respetado"
  DecidedOn: 2026-09-28

VIS-012:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-001]
  Question: "Â¿CÃ³mo quieres distribuir la interfaz? (sidebar, barra inferior, reproductor central, layout tipo dashboard, otro)"
  Guidance: "Mostrar un esquema ASCII de cada opciÃ³n y cÃ³mo se adapta a mobile."
  Answer: "B - Reproductor central + lista debajo (2026-09-28) â†’ rediseÃ±ado a grid bento de tiles (reproductor, cola y fuentes) conservando ese orden en mÃ³vil apilado; ver VIS-013"
  DecidedOn: 2026-10-02

VIS-013:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-001, VIS-005, VIS-012, FRONT-001]
  Question: "Â¿Apruebas el rediseÃ±o completo del frontend con estilo espacial + bento grid y el stack de UI asociado?"
  Guidance: "Tailwind v4 + HeroUI v3 (componentes), Vengence UI (border beam y perspective grid) y Skiper UI (progressive blur de la cabecera), solo planes gratuitos. Acento violeta nebulosa #A855F7; los botones primarios con texto usan #7C3AAD para cumplir contraste AA. Skiper UI exige atribuciÃ³n en la versiÃ³n gratuita: conservada en la cabecera de `src/ui/skiper/progressive-blur.tsx` y registrada aquÃ­."
  Answer: "Si - aprobado: espacio + bento, violeta nebulosa, librerias gratuitas con atribucion a Skiper UI"
  DecidedOn: 2026-10-02
```

### R3 â€” UX Questions

```yaml
UX-001:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-012]
  Question: "Â¿CÃ³mo quieres que se vea la lista de canciones: filas con portada, tarjetas, tabla compacta?"
  Guidance: "Debe permitir ver quÃ© nodo es el actual y, opcionalmente, una visualizaciÃ³n didÃ¡ctica de los nodos enlazados."
  Answer: "A - filas con portada pequeÃ±a y duraciÃ³n"
  DecidedOn: 2026-09-28

UX-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "Â¿Quieres una vista didÃ¡ctica que muestre la lista doblemente enlazada (nodos y flechas prev/next) en tiempo real? Â¿Siempre visible o en un panel opcional?"
  Guidance: "Muy valiosa para sustentaciÃ³n acadÃ©mica. Recomendarla si CONS-001 indica evaluaciÃ³n."
  Answer: "B - vista didÃ¡ctica de nodos alternable con botÃ³n"
  DecidedOn: 2026-09-28

UX-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-012]
  Question: "Â¿CÃ³mo quieres agregar canciones: botÃ³n + modal, panel lateral, arrastrando archivos, buscador de Spotify integrado?"
  Guidance: "Debe cubrir inicio, final y posiciÃ³n arbitraria de forma comprensible."
  Answer: "A - botÃ³n + modal con pestaÃ±as Local/Spotify y selector de posiciÃ³n"
  DecidedOn: 2026-09-28

UX-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-012]
  Question: "Â¿CÃ³mo deben comportarse los mensajes de error/estado (toasts, banners, diÃ¡logos) y quÃ© debe ver el usuario si Spotify no estÃ¡ conectado?"
  Guidance: "Definir estados vacÃ­os, cargando, error y sin conexiÃ³n."
  Answer: "A - toasts + pantalla vacÃ­a ilustrada sin Spotify conectado"
  DecidedOn: 2026-09-28
```

### R4 â€” Player Questions

```yaml
PLAYER-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "Â¿CuÃ¡ntos segundos debe adelantar el botÃ³n de avance?"
  Guidance: "Sugerir 10 s como valor habitual; permitir configurable si el usuario lo desea."
  Answer: "5 segundos"
  DecidedOn: 2026-09-28

PLAYER-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYER-001]
  Question: "Â¿CuÃ¡ntos segundos debe retroceder el botÃ³n de retroceso?"
  Guidance: "Puede ser igual o distinto al avance."
  Answer: "5 segundos"
  DecidedOn: 2026-09-28

PLAYER-002a:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-002]
  Question: "Retroceso de 5 s: si la posiciÃ³n es <= 5 s, Â¿ir a la pista anterior o quedarse en 0:00?"
  Guidance: "A es el comportamiento estÃ¡ndar y evita el conflicto con Previous."
  Answer: "A - si posicion <= 5 s -> pista anterior; si no -> retroceder 5 s"
  DecidedOn: 2026-09-28

PLAYER-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "Â¿Quieres reproducciÃ³n automÃ¡tica de la siguiente canciÃ³n al terminar la actual?"
  Guidance: "Se implementa con el evento de fin de pista + moveNext() de la lista."
  Answer: "A - autoplay a la siguiente (moveNext)"
  DecidedOn: 2026-09-28

PLAYER-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-003]
  Question: "Â¿Quieres reproducciÃ³n aleatoria (shuffle)?"
  Guidance: "Explicar que shuffle sobre una lista enlazada exige una estrategia (permutaciÃ³n de Ã­ndices o reordenar nodos) y cÃ³mo afecta a 'anterior'."
  FollowUps: ["Si sÃ­: crear PLAYLIST-* sobre cÃ³mo se conserva el historial para Previous."]
  Answer: "SÃ­, estrategia (b): lista intacta + Ã­ndice de orden de reproducciÃ³n"
  DecidedOn: 2026-09-28

PLAYER-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-003]
  Question: "Â¿Quieres repetir una canciÃ³n?"
  Guidance: "Modo 'repeat one'."
  Answer: "SÃ­ (repeat one), vÃ­a FEAT-001-d"
  DecidedOn: 2026-09-28

PLAYER-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-003, PLAYLIST-009]
  Question: "Â¿Quieres repetir toda la playlist?"
  Guidance: "Relacionado con si la lista se comporta como circular al llegar a los extremos."
  Answer: "SÃ­ (repeat all como modo en el servicio), vÃ­a FEAT-001-d"
  DecidedOn: 2026-09-28

PLAYER-007:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "Â¿Quieres una barra de progreso interactiva (click y arrastre para hacer seek)?"
  Guidance: "Recomendado; es parte del requisito de seek."
  Answer: "SÃ­ - barra de progreso interactiva (click y arrastre)"
  DecidedOn: 2026-09-28

PLAYER-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "Â¿Quieres control de volumen (slider) y mute?"
  Guidance: "Recomendado. Explicar que en algunos mÃ³viles el volumen lo controla el sistema."
  Answer: "SÃ­ - slider de volumen y mute"
  DecidedOn: 2026-09-28

PLAYER-009:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "Â¿Quieres control de velocidad de reproducciÃ³n?"
  Guidance: "Viable en audio local (playbackRate). El Web Playback SDK de Spotify no ofrece control de velocidad: advertir."
  Answer: "No aplica por CONS-001a (sin control de velocidad)"
  DecidedOn: 2026-09-28

PLAYER-010:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "Â¿Quieres atajos de teclado? Si sÃ­, Â¿cuÃ¡les (espacio = play/pausa, flechas = skip, etc.)?"
  Guidance: "Cuidar accesibilidad y no interferir con campos de texto."
  Answer: "No aplica por FEAT-001-a rechazada (sin atajos de teclado)"
  DecidedOn: 2026-09-28

PLAYER-011:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [ARCH-001, PLAYER-002a]
  Question: "Â¿DÃ³nde vive el estado de reproducciÃ³n (posiciÃ³n actual, seek y skip de 5 s)?"
  Guidance: "Con ARCH-001=A la lista vive en el backend, pero el audio suena en el navegador. Afecta a cÃ³mo se prueba PLAYER-002a."
  Answer: "Backend decide y frontend ejecuta: PlaybackService guarda pista, modos y posicion; el frontend reporta su posicion y envia skip"
  DecidedOn: 2026-09-28
```

### R5 â€” Playlist Questions

```yaml
PLAYLIST-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYER-003]
  Question: "Â¿Quieres una Ãºnica playlist o mÃºltiples playlists?"
  Guidance: "MÃºltiples playlists = una DoublyLinkedList por playlist; impacta en persistencia y UI."
  Answer: "B - varias playlists con persistencia en Postgres"
  DecidedOn: 2026-09-28

PLAYLIST-001a:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [PLAYLIST-001, DB-001]
  Question: "Si Neon (Postgres gratuito) falla o se agota, Â¿quÃ© plan degradado aceptas?"
  Guidance: "Opciones: (a) solo lectura con aviso, (b) reiniciar en memoria y avisar, (c) exportar/importar JSON. Se pregunta antes de F10."
  Answer: null
  DecidedOn: null

PLAYLIST-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres poder crear playlists nuevas?"
  Guidance: "Solo aplica si hay mÃºltiples."
  Answer: "SÃ­ - crear playlists (PlaylistService.create)"
  DecidedOn: 2026-09-28

PLAYLIST-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres renombrar playlists?"
  Guidance: "Solo aplica si hay mÃºltiples."
  Answer: "SÃ­ - renombrar (PlaylistService.rename)"
  DecidedOn: 2026-09-28

PLAYLIST-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres reordenar canciones mediante drag and drop?"
  Guidance: "Explicar que se traduce en removeAt + insertAt (o reenlazado de nodos) y quÃ© costo tiene O(n)."
  Answer: "SÃ­, vÃ­a FEAT-001-e (drag and drop)"
  DecidedOn: 2026-09-28

PLAYLIST-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres favoritos?"
  Guidance: "Puede ser una marca en Song o una playlist especial."
  Answer: "SÃ­, vÃ­a FEAT-001-b (favoritos)"
  DecidedOn: 2026-09-28

PLAYLIST-006:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [PLAYER-003]
  Question: "Â¿Quieres historial de reproducciÃ³n?"
  Guidance: "Distinto de 'anterior' de la lista; explicar diferencia."
  Answer: null
  DecidedOn: null

PLAYLIST-007:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres una cola de reproducciÃ³n (queue) independiente de la playlist?"
  Guidance: "La cola es una estructura distinta (posible uso de Queue); aclarar que no sustituye la lista doblemente enlazada."
  Answer: "No aplica por CONS-001a (sin queue)"
  DecidedOn: 2026-09-28

PLAYLIST-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres bÃºsqueda dentro de la playlist?"
  Guidance: "Usa find(); mencionar O(n)."
  Answer: "SÃ­, vÃ­a FEAT-001-c (bÃºsqueda con find)"
  DecidedOn: 2026-09-28

PLAYLIST-009:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYER-003]
  Question: "Al llegar al final (o al inicio) de la lista, Â¿debe detenerse o dar la vuelta (comportamiento circular)?"
  Guidance: "Circular implica enlazar tailâ†”head o simularlo en la capa de servicio. Explicar cuÃ¡l conserva mejor el concepto puro de lista doblemente enlazada."
  Answer: "A - detenerse en los extremos (tail.next = None)"
  DecidedOn: 2026-09-28

PLAYLIST-009a:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-009]
  Question: "Â¿CÃ³mo seÃ±ala DoublyLinkedList que llegÃ³ al extremo: excepciÃ³n o valor de retorno?"
  Guidance: "SKILL2 admite ambas; documentar la elegida."
  Answer: "Retorna bool (True = se moviÃ³); current no cambia en el extremo. Sin excepciÃ³n"
  DecidedOn: 2026-09-28

PLAYLIST-009b:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-009]
  Question: "Al eliminar el nodo que estÃ¡ en current, Â¿a dÃ³nde pasa current?"
  Guidance: "Afecta a lo que se reproduce tras borrar desde la UI."
  Answer: "Al siguiente; si era tail, al anterior; si era el Ãºnico, current = None"
  DecidedOn: 2026-09-28

PLAYLIST-010:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [LOCAL-001, SPOTIFY-001]
  Question: "Â¿Puede una misma playlist mezclar canciones locales y de Spotify?"
  Guidance: "TÃ©cnicamente posible con dos motores (Strategy), pero implica cambio de player entre pistas; explicar posibles saltos/latencia y pÃ©rdida de gapless."
  Answer: null
  DecidedOn: null

ARCH-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿DÃ³nde debe vivir la lista doblemente enlazada: solo backend Python, solo frontend, o en ambos con contrato de pruebas compartido?"
  Guidance: "Ver secciÃ³n 8.5 de AGEND.md. Explicar A/B/C con ventajas y desventajas y recomendar."
  Answer: "A - DLL solo en backend Python (tramo inicial de C)"
  DecidedOn: 2026-09-28

ARCH-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [ARCH-001]
  Question: "Â¿Aceptas la arquitectura por capas/hexagonal propuesta (domain / application / infrastructure / api) con inyecciÃ³n de dependencias? Â¿Quieres ajustar algo de la estructura de carpetas?"
  Guidance: "Mostrar el Ã¡rbol de la secciÃ³n 8.2 y justificar cada carpeta. La separaciÃ³n y la POO no son negociables; los nombres sÃ­."
  Answer: "SÃ­ - arquitectura hexagonal por capas con DI y Ã¡rbol 8.2"
  DecidedOn: 2026-09-28

ARCH-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [ARCH-002]
  Question: "Â¿Quieres documentar las decisiones como ADRs en docs/adr y diagramas (UML/Mermaid) de clases y secuencia?"
  Guidance: "Refuerza la evidencia de buena arquitectura, Ãºtil para sustentaciÃ³n."
  Answer: "SÃ­ - ADRs en docs/adr y diagramas Mermaid"
  DecidedOn: 2026-09-28
```

### R6 â€” Local Music Questions

```yaml
LOCAL-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿QuÃ© formatos de audio quieres admitir (MP3, WAV, OGG, FLAC, AAC/M4A, otros)?"
  Guidance: "Explicar soporte real por navegador (ej. FLAC/OGG varÃ­an) y la validaciÃ³n por MIME y extensiÃ³n."
  Answer: "A - MP3 y WAV (validaciÃ³n por MIME y extensiÃ³n)"
  DecidedOn: 2026-09-28

LOCAL-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-001]
  Question: "Â¿Quieres permitir seleccionar mÃºltiples archivos a la vez?"
  Guidance: "Atributo multiple del input; definir en quÃ© orden entran a la lista (inicio/final)."
  Answer: "SÃ­ - selecciÃ³n mÃºltiple; entra al final de la lista"
  DecidedOn: 2026-09-28

LOCAL-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-002]
  Question: "Â¿Quieres drag and drop de archivos sobre la aplicaciÃ³n?"
  Guidance: "Complementa el File Picker; no lo reemplaza (accesibilidad y mÃ³vil)."
  Answer: "SÃ­ - drag and drop ademÃ¡s del File Picker"
  DecidedOn: 2026-09-28

LOCAL-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-001]
  Question: "Â¿Quieres obtener automÃ¡ticamente metadata de los archivos (tÃ­tulo, artista, Ã¡lbum, duraciÃ³n)?"
  Guidance: "Se puede leer en el navegador con una librerÃ­a de tags ID3; alternativa: procesar en backend Python (mutagen), pero implicarÃ­a subir el archivo. Explicar la implicaciÃ³n de privacidad."
  Answer: "A - tags ID3 en el navegador (sin subir archivos)"
  DecidedOn: 2026-09-28

LOCAL-005:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [LOCAL-004]
  Question: "Â¿Quieres mostrar la portada extraÃ­da de la metadata?"
  Guidance: "Definir portada por defecto cuando no exista."
  Answer: null
  DecidedOn: null

LOCAL-006:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [LOCAL-001]
  Question: "Â¿Quieres que la mÃºsica local persista despuÃ©s de cerrar el navegador?"
  Guidance: "Explicar: (a) no persistir (simple, se pierde), (b) guardar solo metadatos y pedir re-seleccionar archivos, (c) guardar los blobs en IndexedDB (persistente pero ocupa disco del navegador y tiene cuotas). Recomendar segÃºn el caso."
  FollowUps: ["Si (c): confirmar LOCAL-008 y lÃ­mites de espacio."]
  Answer: "B - solo metadatos; al volver se re-seleccionan los archivos"
  DecidedOn: 2026-09-28

LOCAL-006a:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [LOCAL-006]
  Question: "Â¿CÃ³mo marca la UI los temas cuyo archivo local necesita re-selecciÃ³n?"
  Guidance: "Propuesta: borde Ã¡mbar + badge 'archivo perdido' + acciÃ³n de re-selecciÃ³n. Se pregunta en F5."
  Answer: null
  DecidedOn: null

LOCAL-007:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "Â¿Quieres guardar las playlists localmente (en el navegador)?"
  Guidance: "Diferenciar de la persistencia en servidor (DB-001)."
  Answer: "SÃ­ - playlists tambiÃ©n en el navegador"
  DecidedOn: 2026-09-28

LOCAL-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-006, LOCAL-007]
  Question: "Â¿QuÃ© estrategia de almacenamiento local prefieres (IndexedDB, localStorage, File System Access API, ninguna)?"
  Guidance: "localStorage no sirve para blobs; File System Access API no estÃ¡ en todos los navegadores. Explicar y recomendar (normalmente IndexedDB)."
  Answer: "A - IndexedDB (gratis; ninguna opciÃ³n de pago)"
  DecidedOn: 2026-09-28
```

### R7 â€” Spotify Questions

```yaml
SPOTIFY-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-004]
  Question: "Â¿Ya tienes creada una app en el Spotify Developer Dashboard? Si no, Â¿te guÃ­o para crearla?"
  Guidance: "Explicar quÃ© se configura allÃ­ (Client ID, Redirect URIs, usuarios permitidos). No pedir que pegue secretos en el chat ni en archivos versionados."
  Answer: "App creada; Client ID df3caeb1d0f94b5db0fc0072b248cf53"
  DecidedOn: 2026-09-28

SPOTIFY-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [SPOTIFY-001]
  Question: "Â¿Puedes proporcionar el Client ID (pÃºblico) y confirmar que el Client Secret quedarÃ¡ solo en variables de entorno del backend (nunca en el cÃ³digo ni en el frontend)?"
  Guidance: "Indicar exactamente los nombres de variables: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI."
  Answer: "SÃ­ - Client ID en .env; Client Secret jamÃ¡s en chat ni en cÃ³digo"
  DecidedOn: 2026-09-28

SPOTIFY-003:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [SPOTIFY-001, DEPLOY-001]
  Question: "Â¿CuÃ¡les serÃ¡n las Redirect URIs (local y producciÃ³n)?"
  Guidance: "Verificar en la documentaciÃ³n vigente las reglas de HTTPS/loopback. Deben coincidir exactamente con las registradas."
  Answer: "Dev: http://127.0.0.1:5173/callback Â· Prod: https://migmusic.vercel.app/api/auth/callback"
  DecidedOn: 2026-09-28

SPOTIFY-004:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [DEPLOY-001]
  Question: "Â¿En quÃ© entorno se desplegarÃ¡ (dominio/URL final) para configurar OAuth y CORS correctamente?"
  Guidance: "Se conecta con DEPLOY-001 y DEPLOY-002."
  Answer: "https://migmusic.vercel.app (proxy /api/* hacia Render)"
  DecidedOn: 2026-09-28

SPOTIFY-005:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-004]
  Question: "Para usar el Web Playback SDK se requiere una cuenta Spotify Premium: Â¿confirmas que tendrÃ¡s una para desarrollar y demostrar?"
  Guidance: "Si no, proponer alternativa: modo demo sin reproducciÃ³n Spotify o reproducciÃ³n vÃ­a Spotify Connect; registrar el impacto en el alcance."
  Answer: "SÃ­ - cuenta Premium confirmada (CONS-004)"
  DecidedOn: 2026-09-28

SPOTIFY-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [SPOTIFY-001]
  Question: "Â¿QuÃ© funciones de Spotify quieres exactamente: buscar canciones, ver tus playlists, agregar canciones de bÃºsqueda a la lista, ver tus canciones guardadas?"
  Guidance: "Determina los scopes. Aplicar mÃ­nimo privilegio y verificar disponibilidad vigente de endpoints."
  Answer: "C - buscar, playlists propias, guardadas, seguir artistas/Ã¡lbumes"
  DecidedOn: 2026-09-28

SPOTIFY-007:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [SPOTIFY-002]
  Question: "Â¿CÃ³mo quieres manejar la sesiÃ³n de Spotify (recordar al usuario, cerrar sesiÃ³n, expiraciÃ³n) y quÃ© debe pasar si el token expira mientras suena algo?"
  Guidance: "Propuesta: cookie HttpOnly + refresh automÃ¡tico en backend."
  Answer: "Cookie HttpOnly segura en backend + refresh automÃ¡tico de access token; si falla refresh, cerrar sesiÃ³n y avisar al usuario"
  DecidedOn: 2026-09-28

SPOTIFY-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001]
  Question: "En mÃ³vil, el Web Playback SDK tiene limitaciones de soporte: Â¿aceptas que en dispositivos mÃ³viles Spotify funcione con una alternativa (por ejemplo controlar el reproductor de Spotify vÃ­a Web API) o solo mÃºsica local?"
  Guidance: "Verificar compatibilidad vigente antes de prometer nada. Registrar en ADR."
  Answer: "A - mÃ³vil: mÃºsica local + Spotify vÃ­a Web API (sin SDK en mÃ³vil)"
  DecidedOn: 2026-09-28
```

### R8 â€” Frontend Questions

```yaml
FRONT-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-006, LOCAL-006, SPOTIFY-008]
  Question: "Â¿QuÃ© tecnologÃ­a frontend prefieres (React, Vue, Svelte, otra)?"
  Guidance: "Si no tiene preferencia: comparar brevemente y recomendar una segÃºn la complejidad del estado del reproductor, ecosistema de animaciÃ³n y curva de aprendizaje. Debe permitir estructura POO clara."
  Answer: "A - React + Vite"
  DecidedOn: 2026-09-28

FRONT-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [FRONT-001]
  Question: "Â¿Quieres TypeScript?"
  Guidance: "Recomendar TypeScript: interfaces y clases abstractas hacen mÃ¡s visible la POO y la arquitectura."
  Answer: "SÃ­ - TypeScript"
  DecidedOn: 2026-09-28

FRONT-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "Â¿QuÃ© nivel de animaciÃ³n tÃ©cnica quieres implementar (CSS puro, animaciones por librerÃ­a, canvas/WebGL)?"
  Guidance: "Relacionar con VIS-006 y rendimiento."
  Answer: "A - CSS puro sobre transform/opacity, con prefers-reduced-motion; sin canvas/WebGL"
  DecidedOn: 2026-09-28

FRONT-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-003]
  Question: "Â¿Prefieres alguna librerÃ­a de animaciones (Framer Motion, GSAP, Motion One, anime.js u otra)?"
  Guidance: "Si no, recomendar segÃºn FRONT-001."
  Answer: "Ninguna libreria; CSS puro (cierra FRONT-003 = A)"
  DecidedOn: 2026-09-28

FRONT-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001]
  Question: "Â¿QuÃ© estrategia de estado y estilos prefieres (stores, context, CSS Modules, Tailwind, etc.) o delego la recomendaciÃ³n?"
  Guidance: "Debe respetar la separaciÃ³n de UI y lÃ³gica."
  Answer: "CSS Modules + Zustand (mantiene tokens.css de F1 y da stores minimos para playlist y reproductor)"
  DecidedOn: 2026-09-28

FRONT-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001]
  Question: "Â¿QuÃ© estrategia responsive quieres (mobile-first, breakpoints especÃ­ficos, layout distinto por dispositivo)?"
  Guidance: "Proponer mobile-first con 4 rangos: mobile, tablet, laptop, desktop. Confirmar."
  Answer: "Mobile-first con breakpoints sm 640 / md 1024 / lg 1440; reproductor central y lista debajo (VIS-012)"
  DecidedOn: 2026-09-28
```

### R9 â€” Backend Questions

```yaml
BACK-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [ARCH-002, SPOTIFY-002]
  Question: "Â¿QuÃ© framework Python quieres usar (FastAPI, Flask, Django)?"
  Guidance: "Si no tiene preferencia: FastAPI (tipado, async, validaciÃ³n con Pydantic, OpenAPI automÃ¡tica, bueno para arquitectura limpia); Flask (minimalista, mÃ¡s manual); Django (completo, mÃ¡s pesado, ORM/admin). Explicar y recomendar."
  Answer: "A - FastAPI"
  DecidedOn: 2026-09-28

BACK-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [BACK-001]
  Question: "Â¿QuÃ© versiÃ³n de Python y gestor de dependencias usarÃ¡s (venv+pip, Poetry, uv)?"
  Guidance: "Alinear con CONS-003."
  Answer: "A - uv (fallback a venv+pip si no estÃ¡ disponible)"
  DecidedOn: 2026-09-28

BACK-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [BACK-001]
  Question: "Â¿QuÃ© herramientas de calidad de cÃ³digo quieres (ruff, black, mypy, pre-commit)?"
  Guidance: "Recomendar type hints estrictos para reforzar POO."
  Answer: "A - ruff + mypy estricto"
  DecidedOn: 2026-09-28
```

### R10 â€” Database Questions

```yaml
DB-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYLIST-001, LOCAL-007, BACK-001]
  Question: "Â¿Quieres persistencia de playlists en el servidor (que sobrevivan entre dispositivos y sesiones) o basta con memoria/almacenamiento local?"
  Guidance: "Explicar cuÃ¡ndo REALMENTE se necesita base de datos: mÃºltiples dispositivos, cuentas de usuario, compartir playlists. Si solo hay una sesiÃ³n y datos locales, no es necesaria y aÃ±adirla es sobreingenierÃ­a."
  Answer: "SÃ­ - persistencia de playlists en servidor"
  DecidedOn: 2026-09-28

DB-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DB-001]
  Question: "Si se necesita base de datos: Â¿SQLite, PostgreSQL u otra?"
  Guidance: "SQLite: simple, archivo Ãºnico, ideal en desarrollo/demo pero cuidado con discos efÃ­meros en cloud. PostgreSQL: robusto, apto para producciÃ³n. Recomendar segÃºn DEPLOY-001."
  Answer: "A - PostgreSQL en Neon (plan gratuito)"
  DecidedOn: 2026-09-28

DB-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DB-002]
  Question: "Â¿CÃ³mo se guardarÃ¡ el orden de la lista enlazada en la base de datos (columnas prev/next, campo position, u otra estrategia) y aceptas reconstruir la DoublyLinkedList al cargar?"
  Guidance: "Explicar el mapeo objeto-relacional de una estructura enlazada y sus trade-offs. Mantener el dominio libre de ORM (Repository)."
  Answer: "B - columnas prev_id/next_id reflejando el enlace; DLL se reconstruye al cargar"
  DecidedOn: 2026-09-28

DB-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DB-001]
  Question: "Con playlists guardadas en el servidor, Â¿quiÃ©n puede leerlas y editarlas? No hay cuentas de MigMusic."
  Guidance: "Opciones: (a) sin cuentas, UUID opaco de acceso por enlace; (b) dueÃ±o = sesiÃ³n de Spotify; (c) cuentas propias con registro/login."
  Answer: "A - sin cuentas; UUID opaco. AÃ±adir dueÃ±o despuÃ©s es una columna extra"
  DecidedOn: 2026-09-28
```

### R11 â€” Additional Features Questions

> El agente **debe proponer como mÃ­nimo 2** funcionalidades adicionales y **no agregarlas automÃ¡ticamente**. Para cada propuesta: quÃ© hace, por quÃ© es Ãºtil, complejidad aproximada e impacto en la arquitectura. Candidatas: Shuffle, Repeat, Favorites, History, Queue, Search, Filters, Audio visualizer, Equalizer, Keyboard shortcuts, Multiple playlists, Sleep timer, Playback speed. (Excluir las que el usuario ya haya aceptado/rechazado antes.)

```yaml
FEAT-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [R4, R5, R6, R7]
  Question: "Te propongo estas funcionalidades adicionales (con explicaciÃ³n de cada una). Â¿CuÃ¡les quieres incluir? (mÃ­nimo 2 para cumplir el taller)"
  Guidance: "Presentar tabla: funcionalidad | quÃ© hace | utilidad | complejidad | impacto arquitectÃ³nico. Registrar cada una como sub-entrada FEAT-001-<nombre> con CONFIRMED o REJECTED."
  Answer: "Elegidas b, c, d, e (4 funcionalidades; mÃ­nimo 2 requerido)"
  DecidedOn: 2026-09-28

FEAT-001-a:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Atajos de teclado (espacio, flechas)"
  Guidance: "Descartada por el usuario."
  Answer: "REJECTED"
  DecidedOn: 2026-09-28

FEAT-001-b:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Favoritos: marcar canciÃ³n con corazÃ³n (flag en Song + vista)"
  Guidance: "Bajo coste, impacto en Song + UI."
  Answer: "CONFIRMED"
  DecidedOn: 2026-09-28

FEAT-001-c:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "BÃºsqueda dentro de la playlist usando find()"
  Guidance: "Bajo coste, usa la lista (O(n))."
  Answer: "CONFIRMED"
  DecidedOn: 2026-09-28

FEAT-001-d:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Repeat one / repeat all (modos en PlaybackService)"
  Guidance: "Bajo coste; coherente con PLAYLIST-009=A."
  Answer: "CONFIRMED"
  DecidedOn: 2026-09-28

FEAT-001-e:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Reordenar con drag and drop (removeAt + insertAt)"
  Guidance: "Coste medio; impacto en UI + lista."
  Answer: "CONFIRMED"
  DecidedOn: 2026-09-28

FEAT-002:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Â¿Alguna funcionalidad propia que quieras agregar y que no estÃ© en la lista?"
  Guidance: "Evaluar impacto y clasificarla."
  Answer: null
  DecidedOn: null

FEAT-003:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Para las funcionalidades aceptadas, Â¿en quÃ© orden de prioridad las implementamos?"
  Guidance: "Reflejar en el Roadmap."
  Answer: null
  DecidedOn: null

FEAT-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Letras de la cancion: YouTube Music (fuente propia) y LRCLIB para Spotify/local?"
  Guidance: "Diseno previo recuperado de los .pyc: entidad Lyrics, puerto LyricsProvider, LyricsService con estrategia (fuente propia -> LRCLIB) y cache TTL; POST /api/lyrics con 204 cuando no hay letras. El adapter LRCLIB nunca llego a existir."
  Answer: "CONFIRMED - implementar en la rama feature/background-play-and-security"
  DecidedOn: 2026-10-03

FEAT-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Reproduccion en segundo plano (Media Session + PWA) y reproduccion inmediata al pulsar una cancion?"
  Guidance: "Media Session API con metadata y controles; manifest + service worker sencillo sin cachear /api/*; clic optimista, cancelacion de peticiones obsoletas, reutilizacion de reproductores y precarga de la siguiente pista. Limitacion aceptada: el iframe de YouTube se pausa al bloquear el movil (no evitable de forma legitima)."
  Answer: "CONFIRMED - rama feature/background-play-and-security"
  DecidedOn: 2026-10-03

SEC-001:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "Endurecimiento de seguridad: rate limiting, cabeceras, validacion estricta, auditoria de dependencias y modo produccion?"
  Guidance: "Rate limiting por X-Device-Id (principal) + IP (respaldo), estricto en endpoints costosos (busqueda, letras, YouTube Music), 429 con Retry-After, desactivado en desarrollo/tests. CSP probada con E2E y ajustada a YouTube/Spotify; HSTS, nosniff, Referrer-Policy, frame-ancestors; validacion de tipos/longitudes/tamano de cuerpo; autorizacion por owner_id en todos los recursos."
  Answer: "CONFIRMED - rama feature/background-play-and-security"
  DecidedOn: 2026-10-03
```

### R12 â€” Deployment Questions

```yaml
DEPLOY-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-005, FRONT-001, BACK-001, DB-001]
  Question: "Â¿DÃ³nde quieres desplegar MigMusic (Vercel, Render, Railway, Fly.io, AWS, Azure, Google Cloud, otro)?"
  Guidance: "Si no tiene preferencia: recomendar una arquitectura (ej. frontend estÃ¡tico en Vercel/Netlify + backend Python en Render/Railway/Fly.io + PostgreSQL gestionado si aplica), explicando por quÃ©, costos y limitaciones (arranque en frÃ­o, disco efÃ­mero)."
  Answer: "A - Vercel (frontend) + Render (backend)"
  DecidedOn: 2026-09-28

DEPLOY-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [DEPLOY-001]
  Question: "Â¿Frontend y backend estarÃ¡n en el mismo dominio (o subdominios) o en dominios distintos?"
  Guidance: "Determina CORS, cookies SameSite y la Redirect URI de Spotify."
  Answer: "X - proxy /api/* en Vercel: un solo origen (migmusic.vercel.app)"
  DecidedOn: 2026-09-28

DEPLOY-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DEPLOY-001]
  Question: "Â¿Quieres CI/CD (GitHub Actions) con despliegue automÃ¡tico al hacer push?"
  Guidance: "Recomendar como mÃ­nimo: lint + tests en cada PR."
  Answer: "SÃ­ - GitHub Actions con lint y tests que bloquean"
  DecidedOn: 2026-09-28

DEPLOY-004:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [DEPLOY-001]
  Question: "Â¿Quieres contenedores Docker para desarrollo y producciÃ³n?"
  Guidance: "Ayuda a reproducibilidad; puede ser obligatorio segÃºn la plataforma."
  Answer: "No aplica por CONS-003 (entorno sin Docker)"
  DecidedOn: 2026-09-28

DEPLOY-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DEPLOY-001]
  Question: "Â¿QuÃ© nivel de logs y monitoreo quieres (logs estructurados, healthcheck, alertas)?"
  Guidance: "Nunca registrar tokens ni datos sensibles."
  Answer: "Vercel: miguelcebing; Render y Neon conectadas vÃ­a GitHub. Logs estructurados bÃ¡sicos + healthcheck (recomendado, 0 $)"
  DecidedOn: 2026-09-28
```

### R13 â€” Testing Questions

```yaml
TEST-001:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001, BACK-001]
  Question: "Â¿QuÃ© herramientas de prueba prefieres (pytest en backend; Vitest/Jest y Playwright/Cypress en frontend) o delego la recomendaciÃ³n?"
  Guidance: "Recomendar pytest + herramienta nativa del bundler + Playwright."
  Answer: "A - pytest + Vitest + Playwright"
  DecidedOn: 2026-09-28

TEST-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [TEST-001]
  Question: "Â¿QuÃ© cobertura mÃ­nima esperas (por ejemplo â‰¥ 90 % en el dominio y la lista doblemente enlazada)?"
  Guidance: "Proponer umbrales por capa."
  Answer: "â‰¥95% en domain/ (nÃºcleo acadÃ©mico) y â‰¥80% global; el CI lo bloquea"
  DecidedOn: 2026-09-28

TEST-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DEPLOY-003]
  Question: "Â¿Quieres que las pruebas se ejecuten automÃ¡ticamente en CI y bloqueen el despliegue si fallan?"
  Guidance: "Recomendado."
  Answer: "SÃ­ - los tests corren en CI y bloquean (implÃ­cito en DEPLOY-003)"
  DecidedOn: 2026-09-28

TEST-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [TEST-001]
  Question: "Â¿Quieres tests property-based con hypothesis para los invariantes de la lista?"
  Guidance: "SKILL2 lo propone como opcional; aÃ±ade una dependencia de desarrollo."
  Answer: "SÃ­ - hypothesis para invariantes y secuencias aleatorias"
  DecidedOn: 2026-09-28
```

---

## Implementation Gate

El agente **NO** escribe cÃ³digo de aplicaciÃ³n (mÃ¡s allÃ¡ de exploraciÃ³n o prototipos descartables explÃ­citamente anunciados) hasta que se cumplan **todas** estas condiciones:

- [x] Todas las preguntas con `Priority: CRITICAL` estÃ¡n en `CONFIRMED` o `REJECTED`.
- [x] **Arquitectura:** `ARCH-001`, `ARCH-002` confirmadas.
- [x] **Frontend:** `FRONT-001`, `FRONT-002` confirmadas.
- [x] **Backend:** `BACK-001` confirmada (Python).
- [x] **Spotify:** `SPOTIFY-001`â€¦`SPOTIFY-005` confirmadas.
- [x] **ReproducciÃ³n local:** `LOCAL-001`, `LOCAL-006` confirmadas.
- [x] **DiseÃ±o principal:** `VIS-001`, `VIS-006`, `VIS-012`, `VIS-013` confirmadas.
- [x] **Estrategia de playlist:** `PLAYLIST-001`, `PLAYLIST-009` confirmadas.
- [x] **Lista doblemente enlazada:** ubicaciÃ³n (`ARCH-001`) y comportamiento en extremos (`PLAYLIST-009`) confirmados.
- [x] **Deployment:** `DEPLOY-001`, `DEPLOY-002` confirmadas.
- [x] Ninguna pregunta adicional creada por el agente con prioridad `CRITICAL` sigue `PENDING`.
- [x] El agente ha presentado un **resumen de decisiones** y el usuario ha dicho explÃ­citamente que puede empezar.

**Excepciones:** las preguntas `NORMAL` pendientes **no bloquean** el gate; se preguntan en la fase del roadmap donde se necesiten (registrando el momento en el Decision Log).

---

## Reglas para decisiones tÃ©cnicas

Cuando surja una decisiÃ³n tÃ©cnica no definida, el agente:

1. Explica **brevemente** las opciones.
2. Expone **ventajas y desventajas** de cada una.
3. **Recomienda** una opciÃ³n tÃ©cnicamente razonable y dice por quÃ©.
4. **Pregunta** cuÃ¡l prefiere el usuario.
5. **Registra** la decisiÃ³n (Answer + Decision Log + ADR si es arquitectÃ³nica).

Nunca asume la elecciÃ³n del usuario. Si el usuario delega ("lo que recomiendes"), la recomendaciÃ³n pasa a `PROPOSED` y se pide un "sÃ­" explÃ­cito.

## InterpretaciÃ³n de respuestas

- **Respuesta clara:** registrar literal + resumen, `CONFIRMED`.
- **Respuesta ambigua:** reformular con una pregunta de confirmaciÃ³n; mantener `PROPOSED`.
- **Respuesta parcial:** confirmar la parte resuelta; crear sub-pregunta `-a` para la pendiente.
- **Respuesta contradictoria con otra decisiÃ³n:** seÃ±alar el conflicto, explicar consecuencias y pedir que elija; actualizar ambas.
- **"No quiero X":** `REJECTED`; no volver a proponer.
- **Cambio de opiniÃ³n posterior:** reabrir (`CONFIRMED â†’ PENDING`), evaluar impacto en cÃ³digo ya escrito y en el gate, registrar en Decision Log.

## Preguntas adicionales (cuÃ¡ndo crearlas)

El agente crea nuevas preguntas cuando:

- Una respuesta introduce una tecnologÃ­a o funcionalidad nueva sin decisiones asociadas.
- Hay una incompatibilidad tÃ©cnica descubierta (ej. visualizador de audio con Spotify SDK).
- Aparece una limitaciÃ³n de las plataformas (Spotify, navegadores, cloud) que cambia el alcance.
- La respuesta del usuario es demasiado vaga para implementar.
- Se descubre una dependencia entre decisiones no prevista.

ConvenciÃ³n de IDs nuevos: `<PREFIJO>-<nÃºmero>` siguiente disponible, o sufijo de letra (`LOCAL-006a`) cuando derive de otra.

---

## Roadmap

> Las fases se ajustan tras la entrevista. Cada fase termina con pruebas verdes y actualizaciÃ³n de este archivo.

| Fase | Contenido | Skills |
|---|---|---|
| **F0 â€” Entrevista y gate** | Rondas R1â€“R13, resumen de decisiones, aprobaciÃ³n para empezar. | `requirements-interview` |
| **F1 â€” Fundaciones** | Repositorio, estructura de carpetas (8.2), tooling, config por entorno, logging, CI base. | `backend-architecture-python`, `testing-quality` |
| **F2 â€” NÃºcleo de dominio** | `Node`, `DoublyLinkedList`, `Song`, `Playlist` + suite de pruebas completa. | `doubly-linked-list`, `testing-quality` |
| **F3 â€” Servicios y API** | `PlaylistService`, `PlaybackService`, rutas, schemas, manejo de errores. | `backend-architecture-python` |
| **F4 â€” Frontend base** | Layout, design tokens, componentes, cliente API, controladores. | `ui-ux-design` |
| **F5 â€” Audio local** | `LocalAudioPlayer`, File Picker, seek, skip N seg, volumen, persistencia si se aprobÃ³. | `local-audio` |
| **F6 â€” Spotify** | OAuth, sesiÃ³n, bÃºsqueda, `SpotifyPlayer` con Web Playback SDK, manejo de errores. | `spotify-integration` |
| **F7 â€” IntegraciÃ³n** | Playlist unificada, cambio entre players, vista didÃ¡ctica de la lista. | todas |
| **F8 â€” Funcionalidades adicionales** | Las aprobadas en `FEAT-*`. | segÃºn cada una |
| **F9 â€” Pulido** | Animaciones, responsive, accesibilidad, rendimiento. | `ui-ux-design` |
| **F10 â€” Despliegue** | Cloud, HTTPS, CORS, Redirect URI de producciÃ³n, logs. | `deployment-cloud` |
| **F11 â€” Cierre** | E2E, documentaciÃ³n final, checklist de aceptaciÃ³n, demo. | `testing-quality` |

---

## Criterios de aceptaciÃ³n

**Lista doblemente enlazada**
- [x] `Node`/`DoublyLinkedList` implementados con enlaces reales `previous`/`next`, `head`, `tail`, `current`, `size`.
- [x] Todas las operaciones mÃ­nimas de la secciÃ³n 9 implementadas y probadas, incluidos casos borde.
- [x] La playlist activa usa la lista (no un array) y el agente puede explicar cÃ³mo.

**Reproductor**
- [x] Play, Pause, Next, Previous, Seek, Volume, Mute funcionan con audio real. (E2E `master-flow`, desktop + mÃ³vil, con WAV real)
- [x] Skip forward y skip backward mueven exactamente N segundos configurados (`PLAYER-001/002`) sin salirse de los lÃ­mites de la pista. (E2E + unit tests de `PlaybackService`/clamp)
- [x] Agregar (inicio/final/posiciÃ³n), eliminar y seleccionar canciÃ³n funcionan desde la UI. (E2E: 3 pistas, insert en Ã­ndice 1, quitar la activa)

**Fuentes**
- [x] MÃºsica local: File Picker, reproducir/pausar/seek/cambiar/eliminar. (E2E con `setInputFiles`)
- [ ] Spotify: login OAuth completo, refresh de token, reproducciÃ³n con Web Playback SDK (con cuenta Premium), errores manejados. *(2026-10-01: callback verificado en producciÃ³n â€” `state` firmado sin cookie llega hasta Spotify (antes: 401), cookie + `state` falsificado â†’ 422, sin nada â†’ 401; la respuesta `invalid_grant` y no `invalid_client` confirma credenciales reales de la app. Queda la demo manual con cuenta Premium: autorizar, buscar y reproducir con el Web Playback SDK)*
- [x] Spotify y local se tratan como fuentes separadas y polimÃ³rficas. (`AudioSource` en F5, unit tests de `SpotifyPlayer`/`LocalAudioPlayer`)

**Arquitectura y cÃ³digo**
- [x] Estructura por capas visible y respetada (sin lÃ³gica en rutas/componentes).
- [x] POO: abstracciones (ABC/interfaces), polimorfismo, inyecciÃ³n de dependencias, SOLID justificable. (`create_app` + repositorios/polimorfismo de reproducciÃ³n, ADR-001/005)
- [x] Backend 100 % Python. CÃ³digo en inglÃ©s.
- [x] Sin secretos en repositorio ni en frontend; `.env.example` presente.

**Interfaz**
- [x] Refleja las decisiones `VIS-*`/`UX-*` confirmadas; animaciones acordes; `prefers-reduced-motion` respetado. (`tokens.css` + Framer Motion con `MotionConfig reducedMotion="user"`, F9-GATE/F4-ANIM)
- [x] Responsive verificado en mobile, tablet, laptop y desktop. (breakpoints 640/1024/1440 + E2E en Pixel 7)
- [x] Accesibilidad bÃ¡sica cumplida (teclado, foco, ARIA, contraste). (axe WCAG 2.1 A/AA sin violaciones + focus-trap en E2E)

**Calidad y despliegue**
- [x] Pruebas unitarias/integraciÃ³n/e2e pasando; cobertura acorde a `TEST-002`. (317 pytest/97.06 %/dominio 100 %, 80 Vitest, 9 E2E; ver `docs/testing.md`)
- [x] Desplegado en la nube con HTTPS, CORS correcto, Redirect URI de producciÃ³n, logs y configuraciÃ³n de producciÃ³n. *(verificado 2026-10-01 sobre `19e9408`: `https://migmusic.vercel.app` â†’ proxy `/api/*` â†’ `https://migmusic-api.onrender.com`; health 200 directo y por proxy, preflight 200 con ACAO `https://migmusic.vercel.app` + `credentials: true`, Spotify acepta la Redirect URI registrada, Render y Vercel auto-desplegaron el push y el workflow `keep-alive` vigila `/api/health` cada 10 min)*
- [x] Al menos 2 funcionalidades adicionales aprobadas por el usuario e implementadas. (`FEAT-001-b/c/d/e`: favoritos, bÃºsqueda, repeat, drag & drop)
- [x] DocumentaciÃ³n (README, docs/architecture, ADRs) actualizada.

---

## Decision Log

> El agente aÃ±ade una lÃ­nea por cada decisiÃ³n o cambio. Formato: `AAAA-MM-DD | ID | DecisiÃ³n | Motivo/Impacto`.

| Fecha | ID | DecisiÃ³n | Motivo / Impacto |
|---|---|---|---|
| 2026-09-28 | CONS-001 | AcadÃ©mico + producto; lÃ­mite 2026-10-02 | Fija plazo: 4 dÃ­as, recorte de alcance negociado |
| 2026-09-28 | CONS-002 | Trabajo solo | Sin revisiÃ³n por pares; nivel en CONS-002a |
| 2026-09-28 | CONS-003 | Windows/VS Code/Python 3.11-3.13/Node 26; sin Docker | DEPLOY-004 pasa a REJECTED; scripts .ps1 |
| 2026-09-28 | CONS-004 | Cuenta Spotify Premium disponible | Web Playback SDK viable en desktop |
| 2026-09-28 | CONS-005 | Solo planes gratuitos | Vercel + Render + Neon free; UptimeRobot |
| 2026-09-28 | CONS-006 | Interfaz en espaÃ±ol e inglÃ©s | AÃ±ade capa i18n en F4 |
| 2026-09-28 | CONS-001a | Alcance A (recomendado) | RNF/FEAT recortadas; 4 FEAT en F8 |
| 2026-09-28 | VIS-001 | Estilo retro/vinilo | Define tokens y microinteracciones |
| 2026-09-28 | VIS-002 | Tema dual con selector | Dos paletas de design tokens |
| 2026-09-28 | VIS-003 | Azul marino/elÃ©ctrico + negro | Base de la paleta |
| 2026-09-28 | VIS-004 | #1E6BFF + #4338CA sobre #0A0D14 | Design tokens F4 |
| 2026-09-28 | VIS-005 | Sin gradientes | Ahorro de implementaciÃ³n |
| 2026-09-28 | VIS-006 | Animaciones sutiles | CSS/WAAPI + prefers-reduced-motion |
| 2026-09-28 | VIS-007 | Sin visualizador | Excluido por CONS-001a |
| 2026-09-28 | VIS-008 | Sin waveform | Excluido por CONS-001a |
| 2026-09-28 | VIS-012 | Layout B: reproductor central + lista | Estructura de layouts F4 |
| 2026-09-28 | UX-001 | Filas con portada | Componente SongRow |
| 2026-09-28 | UX-002 | Vista de nodos alternable | Panel didÃ¡ctico para sustentaciÃ³n |
| 2026-09-28 | UX-003 | Modal con pestaÃ±as Local/Spotify + posiciÃ³n | Cubre RF-07 Ã­ntegro |
| 2026-09-28 | UX-004 | Toasts + estado vacÃ­o | Manejo de errores global |
| 2026-09-28 | PLAYER-001 | Avanzar 5 s | Constante SKIP_FORWARD_SECONDS |
| 2026-09-28 | PLAYER-002 | Retroceder 5 s | Constante SKIP_BACKWARD_SECONDS |
| 2026-09-28 | PLAYER-002a | Si posicion <= 5 s -> pista anterior | Regla de borde en PlaybackService |
| 2026-09-28 | PLAYER-003 | Autoplay con moveNext | evento ended + moveNext |
| 2026-09-28 | PLAYER-004 | Shuffle por Ã­ndice (estrategia b) | Lista intacta; historial separado |
| 2026-09-28 | PLAYER-005 | Repeat one | Modo en PlaybackService |
| 2026-09-28 | PLAYER-006 | Repeat all | Modo en servicio, no circularidad |
| 2026-09-28 | PLAYER-007 | Barra interactiva | RF-05 |
| 2026-09-28 | PLAYER-008 | Volumen + mute | RF-06 |
| 2026-09-28 | PLAYER-009 | Sin velocidad | Excluido por CONS-001a |
| 2026-09-28 | PLAYER-010 | Sin atajos | FEAT-001-a rechazada |
| 2026-09-28 | PLAYLIST-001 | Varias playlists + Postgres | Impacta DB, UI y ARCH |
| 2026-09-28 | PLAYLIST-004 | Drag and drop | FEAT-001-e |
| 2026-09-28 | PLAYLIST-005 | Favoritos | FEAT-001-b |
| 2026-09-28 | PLAYLIST-007 | Sin queue | Excluido por CONS-001a |
| 2026-09-28 | PLAYLIST-008 | BÃºsqueda con find | FEAT-001-c |
| 2026-09-28 | PLAYLIST-009 | Parada en extremos | DLL no circular; repeat como modo |
| 2026-09-28 | ARCH-001 | DLL solo en backend Python | Decisiones de red en Next/Previous; tramo inicial de C |
| 2026-09-28 | ARCH-002 | Hexagonal por capas + DI | Estructura Â§8.2 fijada |
| 2026-09-28 | ARCH-003 | ADRs + Mermaid | Evidencia para sustentaciÃ³n |
| 2026-09-28 | LOCAL-001 | MP3 + WAV | ValidaciÃ³n MIME/extensiÃ³n |
| 2026-09-28 | LOCAL-002 | SelecciÃ³n mÃºltiple | Orden: al final |
| 2026-09-28 | LOCAL-003 | Drag and drop de archivos | Complementa File Picker |
| 2026-09-28 | LOCAL-004 | ID3 en navegador | Privacidad: no se suben archivos |
| 2026-09-28 | LOCAL-006 | Solo metadatos + re-selecciÃ³n | Sin blobs; LOCAL-006a pendiente |
| 2026-09-28 | LOCAL-007 | Playlists tambiÃ©n en navegador | IndexedDB como respaldo |
| 2026-09-28 | LOCAL-008 | IndexedDB | Almacenamiento local gratuito |
| 2026-09-28 | SPOTIFY-001 | App creada; Client ID df3caeb... | Base de OAuth |
| 2026-09-28 | SPOTIFY-002 | Secretos solo en variables de entorno | RNF-07 |
| 2026-09-28 | SPOTIFY-003 | 127.0.0.1:5173 y vercel.app/api/auth/callback | localhost prohibido desde 27/11/2025 |
| 2026-09-28 | SPOTIFY-004 | ProducciÃ³n en migmusic.vercel.app | CORS y OAuth sobre un origen |
| 2026-09-28 | SPOTIFY-005 | Premium confirmada | SDK habilitado en desktop |
| 2026-09-28 | SPOTIFY-006 | Alcance C (buscar, playlists, guardadas, seguir) | Scopes a verificar en F6 |
| 2026-09-28 | SPOTIFY-008 | MÃ³vil sin SDK, vÃ­a Web API | Polimorfismo de players |
| 2026-09-28 | FRONT-001 | React + Vite | Base del frontend |
| 2026-09-28 | FRONT-002 | TypeScript | POO visible y verificable |
| 2026-09-28 | BACK-001 | FastAPI | ValidaciÃ³n Pydantic + OpenAPI |
| 2026-09-28 | BACK-002 | uv | pyproject.toml Ãºnico |
| 2026-09-28 | BACK-003 | ruff + mypy estricto | RNF-04/08 |
| 2026-09-28 | DB-001 | Persistencia en servidor | Postgres obligatorio por PLAYLIST-001 |
| 2026-09-28 | DB-002 | Neon (gratuito) | Sobrevive a discos efÃ­meros de Render |
| 2026-09-28 | DB-003 | prev_id/next_id + reconstrucciÃ³n | Mantiene el dominio libre de ORM |
| 2026-09-28 | FEAT-001 | Elegidas b, c, d, e | Cumple mÃ­nimo de 2 del taller |
| 2026-09-28 | FEAT-001-a | Atajos: REJECTED | Fuera de alcance |
| 2026-09-28 | FEAT-001-b | Favoritos: CONFIRMED | F8 |
| 2026-09-28 | FEAT-001-c | BÃºsqueda: CONFIRMED | F8 |
| 2026-09-28 | FEAT-001-d | Repeat: CONFIRMED | F8 |
| 2026-09-28 | FEAT-001-e | Drag and drop: CONFIRMED | F8 |
| 2026-09-28 | DEPLOY-001 | Vercel + Render | Arquitectura de despliegue |
| 2026-09-28 | DEPLOY-002 | Proxy /api/* en Vercel | Un origen: sin CORS ni SameSite=None |
| 2026-09-28 | DEPLOY-003 | CI con GitHub Actions | Lint + tests bloquean |
| 2026-09-28 | DEPLOY-004 | Sin Docker | No aplica por CONS-003 |
| 2026-09-28 | DEPLOY-005 | Cuentas Vercel(miguelcebing)/Render/Neon vÃ­a GitHub | Listo para F10 |
| 2026-09-28 | TEST-001 | pytest + Vitest + Playwright | F11 |
| 2026-09-28 | TEST-003 | CI bloquea el despliegue | Calidad por fase |
| 2026-09-28 | GATE | Implementation Gate aprobado por el usuario (sÃ­ empieza) | Autoriza F1+; entrevista F0 completada |
| 2026-09-28 | D0-INIT | Repo inicial: .gitignore / .env.example / README / .gitattributes | Secretos fuera de git; primer push a GitHub |
| 2026-09-28 | D0-TREE | AGEND.md a la raÃ­z y .agents/ -> docs/skills/ | ARCH-002: coincide con el Ã¡rbol 8.2 aprobado |
| 2026-09-28 | F1-TOOL | uv + ruff + mypy estricto + pytest; eslint/tsc/vitest en frontend | BACK-002/003 y TEST-001; el CI bloquea en cada push |
| 2026-09-28 | F1-CORE | Settings falla al arrancar si falta una variable obligatoria | SKILL1 Â§4; el Client Secret jamÃ¡s llega al frontend |
| 2026-09-28 | F1-LOG | Logging JSON por lÃ­nea con redacciÃ³n de claves sensibles | DEPLOY-005; nunca se registran tokens |
| 2026-09-28 | F1-HTTP | error_handlers.py Ãºnico: excepciones de dominio -> HTTP | SOLID; los routers no capturan excepciones |
| 2026-09-28 | F1-PROXY | Vite proxy /api -> 127.0.0.1:8000 en desarrollo | Un solo origen tambiÃ©n en local, como en producciÃ³n |
| 2026-09-28 | F1-CI | GitHub Actions: backend + frontend + chequeo de secretos | DEPLOY-003 y TEST-003: bloquean el despliegue |
| 2026-09-28 | F1-DOCS | ADR-001..004 + architecture.md con diagramas Mermaid | ARCH-003; evidencia para la sustentaciÃ³n |
| 2026-09-28 | TEST-002 | Cobertura â‰¥95% dominio y â‰¥80% global | Umbrales en pyproject + CI |
| 2026-09-28 | PLAYLIST-009a | Extremos retornan bool, sin excepciÃ³n | Flujo normal sin try/except |
| 2026-09-28 | PLAYLIST-009b | Al borrar current, pasa a next (o prev si era tail) | No se pierde la posiciÃ³n en la UI |
| 2026-09-28 | PLAYLIST-002 | Crear playlists habilitado | Requerido por PLAYLIST-001=B |
| 2026-09-28 | PLAYLIST-003 | Renombrar playlists habilitado | Requerido por PLAYLIST-001=B |
| 2026-09-28 | TEST-004 | Tests property-based con hypothesis | Invariantes de la lista verificables |
| 2026-09-28 | F2-DLL | Node + DoublyLinkedList con nodos reales (prohibido array) | ARCH-001=A y secciÃ³n 9; invariantes verificables en cada operaciÃ³n |
| 2026-09-28 | F2-EDGE | move_next/move_previous retornan bool y paran en los extremos | PLAYLIST-009=A + 009a; sin excepciones en el flujo normal |
| 2026-09-28 | F2-CURSOR | Al borrar current pasa al siguiente (al anterior si era tail) | PLAYLIST-009b; no se pierde la posiciÃ³n al eliminar desde la UI |
| 2026-09-28 | F2-PLAYLIST | Playlist compone la lista; crear y renombrar habilitados | PLAYLIST-001=B, 002 y 003; duplicados permitidos (sin decisiÃ³n en contra) |
| 2026-09-28 | F2-PROP | Suite property-based con hypothesis contra un modelo de referencia | TEST-004; aleatoriedad contrastada con una list() solo en tests |
| 2026-09-28 | F2-GATE | Umbrales de cobertura en el CI: 80% global y 95% en domain/ | TEST-002; hoy 98.8% global y 100% en domain/ |
| 2026-09-28 | F2-ERRORS | Dominio -> HTTP hereda por MRO en error_handlers | SOLID; los routers siguen sin try/except |
| 2026-09-28 | F3-STATE | El backend decide seek/skip; el frontend solo ejecuta y reporta posicion | PLAYER-011; PLAYER-002a se prueba en Python |
| 2026-09-28 | F3-REPO | F3 entrega el puerto PlaylistRepository con InMemory; el SQL llega en F10 | DB-001/002/003 confirmados; API verde sin credenciales de Neon |
| 2026-09-28 | F3-OWNER | Playlists con UUID opaco y sin cuentas de usuario | DB-004; anadir un dueno despues es una columna extra |
| 2026-09-28 | F3-GATE | PlaylistService y PlaybackService + API REST (playlists y playback) | PRD F3; ruff/mypy limpios y cobertura al 100% |
| 2026-09-28 | F4-STYLES | Estado con Zustand y estilos con CSS Modules | FRONT-005; conserva tokens.css de F1 y la separacion UI/logica |
| 2026-09-28 | F4-RESPONSIVE | Mobile-first con breakpoints 640 / 1024 / 1440 | FRONT-006 con VIS-012 (reproductor central + lista debajo) |
| 2026-09-28 | F4-ANIM | Microinteracciones en CSS puro, sin libreria de animaciones | VIS-009/010/011 + FRONT-003/004; VIS-006 (sutiles) y reduced-motion |
| 2026-09-28 | F4-GATE | Layout, tokens, componentes, API client y controladores completos | FRONT-005/006, VIS-001/002/003/004/006/012, UX-001/002/003/004; build OK, typecheck OK, lint OK |
| 2026-09-28 | F5-GATE | AudioPlayer + LocalAudioPlayer + metadata + IndexedDB | LOCAL-001/002/003/003a/004; build OK, typecheck OK, lint OK, tests OK |
| 2026-09-28 | F6-GATE | OAuth PKCE + sesiÃ³n HttpOnly + proxy Web API + SpotifyPlayer (Web Playback SDK) | SPOTIFY-001/002/003/005/006/007/008, F6-STATE, F6-SCOPES, ADR-005; backend: ruff/mypy/262 tests; frontend: typecheck/lint/40 tests/build OK |
| 2026-09-28 | F6-STATE | SesiÃ³n Spotify con cookie HttpOnly + refresh automÃ¡tico en backend | SPOTIFY-007; token en backend, nunca en frontend |
| 2026-09-28 | F6-SCOPES | Scopes: streaming, user-read-*, user-modify-playback-state, playlist-read-private, user-library-read | SPOTIFY-006 opciÃ³n C; mÃ­nima privilegio |
| 2026-09-28 | F7-GATE | PlaybackController reescrito: seek/skip audibles, fin de pista con repeat, cambio local<->Spotify sin doble audio, volumen en vivo y vista didÃ¡ctica animada | RF-12, PLAYER-001..004/007/011, UX-002; backend: ruff/mypy/262 tests/97%; frontend: lint/typecheck/58 tests/build OK |
| 2026-09-29 | F8-GATE | Favoritos (flag en Song + endpoint idempotente), bÃºsqueda con find en la lista (Enter resalta el primer match), repeat verificado y reordenar con drag & drop | FEAT-001-b/c/d/e, PLAYLIST-005/008; backend: ruff/mypy/284 tests/97%; frontend: lint/typecheck/69 tests/build OK |
| 2026-09-29 | F9-GATE | Pulido: contraste AA con tokens *-text por tema, focus trap + aria-current + group label, tema inicial prefers-color-scheme, code-splitting de music-metadata (main 406â†’288 kB), cursor grab, touch targets 44px | RNF-06, RNF-10, VIS-006/012, F4-RESPONSIVE, SKILL5; frontend: lint/typecheck/69 tests/build OK |
| 2026-09-29 | F10-GATE | Despliegue: SqlPlaylistRepository (psycopg, upsert+rewrite en transacciÃ³n, prev_id/next_id + position), render.yaml (blueprint), vercel.json (rewrite /api/* + x-vercel-enable-rewrite-caching: 0), ADR-006 verificaciÃ³n de plataforma | DB-001/002/003/004, DEPLOY-001..005, ADR-003/004/006; backend: ruff/mypy/292 tests/96.96%/dominio 100% |
| 2026-09-29 | F11-GATE | Cierre: suite E2E Playwright (smoke, flujo maestro en desktop + mÃ³vil, accesibilidad axe WCAG 2.1 A/AA), fix del crash de arranque detectado por E2E (`hasTrack` con `playback: null`), job `e2e` en CI, `docs/testing.md` (reporte criterio â†’ evidencia â†’ estado) | TEST-001/002/003/004 y SKILL6; backend: 292 tests/96.96%/dominio 100%; frontend: lint/tsc/69 tests/7 E2E/build; axe: 0 violaciones |
| 2026-09-30 | DEPLOY-GATE | Despliegue real ejecutado: Vercel proyecto `migmusic` (`https://migmusic.vercel.app`, rewrite `/api/*`), Render `migmusic-api` (`srv-dau8psugekts73del56g`, rootDir `backend`, auto-deploy por commit), Neon `MigMusic` (`DATABASE_URL` fuera del repo en `deploy/credentials.env`) | DEPLOY-001..005, ADR-006; health 200 directo y por proxy, CORS preflight 200 con ACAO correcto, deploy `7f256c6` live |
| 2026-09-30 | DEPLOY-FIX | Root Directory `frontend` en el proyecto Vercel (el build de Git ejecutaba `vite build` en la raÃ­z del repo) e integraciÃ³n Git conectada | Auto-deploy de Vercel operativo (commit â†’ Ready en ~13 s y alias `migmusic.vercel.app`); verificado con `60ab478` |
| 2026-10-01 | F4-ANIM | Se revoca la decisiÃ³n de "CSS puro": se instala Framer Motion para las microinteracciones de PlayerControls, TrackList, AddTrackDialog y ProgressBar | Anula la lÃ­nea F4-ANIM del 2026-09-28; MotionConfig `reducedMotion="user"` y los tokens CSS siguen garantizando VIS-006/FRONT-003/004; gates: tsc, eslint, 77 Vitest, build y 8 E2E OK |
| 2026-10-01 | UX-FIX | Tres correcciones: (1) `AddTrackDialog` con `max-height` + cuerpo con scroll, acciones fijas y contador `Agregar (n)`, (2) siguiente/anterior siempre activos â€”clic en el borde = toast informativo y la mÃºsica sigueâ€” y seek Â±5 s en lugar de 10 s, (3) aislamiento de playlists locales por cabecera `X-Device-Id` (`UX-010`: solo playlists, reproductor global, sin cabecera â‡’ vista completa para E2E/smoke, wipe de Neon al cierre) | Plan de 3 fases aprobado; backend: ruff/mypy/327 tests/97.08%/dominio 100%, frontend: lint/tsc/88 tests/build, E2E: 12 (`spotify-dialog`, `transport-edges`, `device-isolation`); auto-deploy Vercel/Render tras el push y smoke en vivo en esta misma entrega |
| 2026-10-01 | PLAYER-GATE | Reproductor en 7 fases: (1) resiliencia ante reinicio del backend â€” `next_index`/`previous_index` en `PlaybackOut`, `404 no_active_playback` con reconstrucciÃ³n de contexto (open + select) y reintento, sync de `activeId` con la playlist que suena al cargar, (2) guarda de secuencia en los reportes de posiciÃ³n (respuestas stale descartadas), (3) UI optimista con rollback en play/pause, seek, Â±5 s, siguiente/anterior (la pista destino se precarga en el reproductor), (4) hÃ­lo principal: selectors por campo en zustand, `position` aislado a 1 Hz, `ProgressBar` auto-suscrito, `memo` en componentes y drag estable por Ã­ndice, (5) limpieza de cÃ³digo muerto (`getPlayback`, `hasUserGesture`, `errorKey`, `addSong`, loaders privados), (6) E2E `playback-reload` y `auto-advance` (WAV de 1 s: la pista 2 arranca sola y la cola se detiene con `repeat=off`), (7) gates y docs | Plan `.opencode/plans/reproductor-perf-fix.md` (aprobado); backend: ruff/mypy/334 tests/97.13%/dominio 100%, frontend: lint/tsc/96 tests/build, E2E: 14 (10 specs); CI + auto-deploy Vercel/Render tras el push |
| 2026-10-01 | PLAYER-FIX | Feedback del usuario tras el PLAYER-GATE: (1) error puntual `Spotify player did not report a device id` â€” `connect()` del SDK pasaba de largo el `ready` con un sondeo de 2 s, dejando un player sin `_deviceId` y creando una segunda instancia (fuga) en el siguiente intento â‡’ `ready` event-driven con tope de 10 s, desconexiÃ³n en fallo, guarda de `generation` y rechazo inmediato de `initialization_error`/`authentication_error`/`account_error`, (2) transporte percibido como "sin vida"/lento â€” `load()` sin `pause()` final, `play()` corto si ya suena y `togglePlaying()` gira el botÃ³n **antes** de `await player.play()` con `rollbackTo` en `send()` | Backend sin cambios; frontend: lint/tsc/103 tests/build, E2E: 14/14; unit nuevos `spotifySdk.test.ts` (6) + "answers the play click before the player has started the audio"; docs `testing.md` Â§3/Â§5 |
| 2026-10-01 | NET-TIMEOUT | Todo request del `apiClient` aborta a los 10 s (`REQUEST_TIMEOUT_MS` con `AbortController`) y el fallo se presenta como `ApiError code="timeout"` â†’ toast localizado `toast.timeout` ("El servidor tardÃ³ demasiado en responder") con rollback del parche optimista; `failureMessage(cause, language)` compartido por los cuatro controllers para que ningÃºn timeout llegue en crudo | Evita botones mudos cuando Render free se duerme; frontend: lint/tsc/108 tests/build, E2E: 14/14; unit `apiClient.test.ts` +4 y resilience +1; docs `testing.md` Â§3/Â§5 |
| 2026-10-02 | SPEED-FIX | Velocidad de respuesta a los botones (feedback tras NET-TIMEOUT): (1) Render free dormido en cada interacciÃ³n â€” el cron `*/10` de `keep-alive.yml` solo disparÃ³ 2 de ~50 runs esperados en 8 h (GitHub descarta jobs programados bajo carga, peor en la hora en punto; medido en frÃ­o: health 8,6 s directo / 25 s por proxy) â‡’ cron `2-59/5 * * * *` (cada 5 min, nunca en :00, editar el archivo re-registra el schedule) + ping de `/api/health` cada 10 min desde `App.tsx` con la pestaÃ±a abierta, (2) un `report` en vuelo anterior al clic pisaba el parche optimista y la UI volvÃ­a a la canciÃ³n vieja mientras la nueva sonaba â‡’ `send()` reserva `lastAppliedSeq = seq` al parchear y `togglePlaying()` reserva antes de `await player.play()`; observaciÃ³n: tras re-registrar el cron en `f51cb79` los 6 slots siguientes no dispararon (0/6) â‡’ el schedule de GitHub no es fiable para este repo, defensa principal = ping del cliente con la pestaÃ±a abierta, UptimeRobot pendiente como capa externa | Backend sin cambios; frontend: lint/tsc/110 tests/build, E2E: 14/14; unit optimistic UI +2; docs `testing.md` Â§3/Â§5 |
| 2026-10-02 | FLAP-FIX | Siguiente/anterior sonaba la canciÃ³n nueva ~2 s y volvÃ­a a la vieja (feedback tras SPEED-FIX, junto al toast de timeout): (1) el `report` de 1 s disparado despuÃ©s del clic llevaba secuencia mayor y, si el `next` seguÃ­a colgado, el backend respondÃ­a con la canciÃ³n anterior y la aplicaciÃ³n Ã­ntegra revertÃ­a store + audio, (2) en timeout el `rollback(snapshot)` restauraba la vieja a ciegas aunque el comando hubiera aterrizado tarde â‡’ `commit()` abre una ventana de identidad (`intentSeq`) que descarta toda respuesta que cambie de canciÃ³n hasta que el transporte asiente (con `guardBelow` para las respuestas que corrÃ­an dentro de la ventana) y los fallos de desenlace desconocido (`timeout`/`network_error`) conservan el estado optimista â€”el siguiente `report` reconcilia con la verdad del backendâ€” en lugar de hacer rollback | Backend sin cambios; frontend: lint/tsc/114 tests/build, E2E: 14/14; unit optimistic UI +4; docs `testing.md` Â§3/Â§5 |
| 2026-10-02 | WARM-FIX | Feedback tras FLAP-FIX (toast de timeout en "Agregar mÃºsica", latencia medida y correos de fallo de Vercel): (1) un segundo proyecto Vercel `frontend` (alias `frontend-miguelceb.vercel.app`, 0 dominios custom en la cuenta) estaba conectado al mismo repo y fallaba en cada push â‡’ `vercel project rm frontend` â€” solo queda `migmusic`, (2) Render free seguÃ­a durmiÃ©ndose (cron de GitHub 0/6 tras re-registrar; medido: proxy 0,7-3 s y frÃ­o 8-25 s > timeout de 10 s) â‡’ self-ping propio cada 10 min desde un task en el lifespan (`infrastructure/keep_alive.py` sobre `RENDER_BACKEND_URL`, cancelado en el shutdown), (3) cada operaciÃ³n SQL abrÃ­a una conexiÃ³n TCP+TLS nueva a Neon (+100-500 ms por llamada) â‡’ pool `psycopg-pool` (min 0 / max 5, commit/rollback por bloque) en `SqlPlaylistRepository` y `SqlTokenStore` con `close()` en el shutdown y en los fixtures de integraciÃ³n, (4) el 504/502 del proxy Vercel seguÃ­a revirtiendo siguiente/anterior â‡’ `isUnknownOutcome` trata `status >= 500` como desenlace desconocido (conserva el optimismo; una negativa real 4xx sigue revirtiendo, corrigiendo el "500 sÃ­ revierte" de la ronda 4); decisiÃ³n: sin bypass del proxy Vercel (la sesiÃ³n es cookie HttpOnly ligada al host) | Plan aprobado por el usuario (incluye borrar `frontend`); backend: ruff/mypy/338 tests/97.05%, frontend: lint/tsc/116 tests/build, E2E: 14/14; unit `test_keep_alive.py` +4 y optimistic UI +2; docs `testing.md` Â§3/Â§5 |
| 2026-10-02 | CURSOR-FIX | Siguiente/anterior sonaba la canciÃ³n nueva ~2 s y volvÃ­a a la primera, solo en producciÃ³n (feedback tras WARM-FIX): causa real en el backend â€” `PlaybackService` nunca persistÃ­a el cursor de la DLL y `SqlPlaylistRepository.find_by_id` reconstruye la playlist en cada lectura (sin columna de cursor, `ADR-004`), asÃ­ que el `report` ~1 s despuÃ©s del clic devolvÃ­a el Ã­ndice 0 (A) y revertÃ­a store + audio; la ventana `intentSeq` de FLAP-FIX no podÃ­a cubrirlo porque ese report se emite **despuÃ©s** de que el transporte asiente; invisible a toda la suite porque in-memory devuelve el mismo objeto â‡’ `_cursors: dict[str, int]` en el servicio con restore en `_find()` (guarda `0 <= cursor < size`) y registro en los 3 puntos de mutaciÃ³n (`select`, `_sync_order_to_cursor`, `_play_order_position`); sin cambios de frontend (los guards de `send()` ya existen y bastan) | Plan `.opencode/plans/playback-next-prev-cursor.md` aprobado; backend: ruff/format/mypy/pytest **345**/97.02 %, frontend sin cambios (116 tests / E2E 14); tests nuevos `test_playback_service.py` +7 con `_RebuildingRepository` (reproduce la semÃ¡ntica SQL) |
| 2026-10-02 | VIS-013 | RediseÃ±o completo del frontend con estilo **espacial + bento grid**: Tailwind v4 + HeroUI v3 (modales, pestaÃ±as, botones, toasts), Vengence UI (border beam, perspective grid) y Skiper UI (progressive blur de la cabecera), solo planes gratuitos; acento violeta nebulosa `#A855F7` con `#7C3AAD` cuando hay texto encima; backdrop fijo de nebulosas y campo estelar | Sustituye el stack de estilo anterior; **atribuciÃ³n a Skiper UI exigida por su licencia gratuita** (cabecera de `src/ui/skiper/progressive-blur.tsx` + esta entrada); gates: lint/tsc/116 Vitest/build y E2E 14/14 con axe WCAG 2.1 A/AA en 0 violaciones |
| 2026-10-02 | VIS-001 | El estilo deja de ser "D - Retro/vinilo" y pasa a "E - Espacio + bento grid" | Anula la lÃ­nea VIS-001 del 2026-09-28; define los tokens, la atmÃ³sfera y las microinteracciones de toda la UI (ver VIS-013) |
| 2026-10-02 | VIS-005 | Se levanta el rechazo de gradientes: se usan **gradientes fijos** (nebulosa y campo estelar) | Anula la lÃ­nea VIS-005 del 2026-09-28; sigue prohibido el gradiente dinÃ¡mico por portada, asÃ­ que no cambia COST de extracciÃ³n de color |
| 2026-10-02 | VIS-012 | El layout "reproductor central + lista debajo" se rediseÃ±a a **grid bento** de tiles (reproductor, cola y fuentes) | Reinterpreta la opciÃ³n B sin romperla: en mÃ³vil apilado el orden sigue siendo reproductor arriba y lista debajo (ver VIS-013) |
| 2026-10-02 | SPOTIFY-004 | DiagnÃ³stico Spotify (Fase 1) antes del merge: el flujo es **Authorization Code + PKCE S256 correcto** y las dos URIs de redirect responden 302 verificado en vivo (dev `http://127.0.0.1:5173/callback`, prod `https://migmusic.vercel.app/api/auth/callback`); Ãºnico gap de cÃ³digo: un **401 de la Web API no disparaba refresh** (solo el proactivo de 60 s) â‡’ `SpotifyAuthService.force_refresh()` + `token_refresher` (ContextVar fijado por `require_spotify_token`) para **reintentar una sola vez** con token nuevo antes de devolver 401, sin tocar routers ni frontend; higiene: `HANDOFF.md` (secretos en claro, sin trackear) aÃ±adido a `.gitignore` y `SPOTIFY_SCOPES` documentado en `.env.example` | Plan aprobado por el usuario (mostrÃ³ el diff antes de aplicarlo); backend: ruff/format/mypy/**pytest 351**/97.06 %, tests nuevos `test_spotify_client.py` +3 y `test_spotify_auth_service.py` +3; no verificable desde el repo (declarado): estado del Dashboard de Spotify (URIs, Development mode/User Management) y cuenta Premium |

| 2026-10-03 | BGSCOPE | Nueva rama `feature/background-play-and-security`: reproduccion en segundo plano (Media Session API + PWA) e inicio inmediato al pulsar una cancion (clic optimista, cancelacion de peticiones obsoletas, reutilizacion de reproductores y precarga) | Alcance solicitado por el usuario; no altera el gate ni las decisiones confirmadas; limitacion aceptada: el iframe de YouTube se pausa al bloquear el movil |
| 2026-10-03 | FEAT-004 | Letras: se reconstruye el diseno hallado en los `.pyc` (entidad `Lyrics`, puerto `LyricsProvider`, `LyricsService` con estrategia fuente-propia -> LRCLIB y cache TTL) + adapter LRCLIB (nuevo, sin claves) + `POST /api/lyrics` con 204 cuando no hay letras; UI nueva en el reproductor | Cubre YouTube Music, Spotify y musica local; un fallo de letras nunca interrumpe la reproduccion |
| 2026-10-03 | SEC-001 | Endurecimiento: rate limiting por `X-Device-Id`+IP (estricto en busqueda/letras/YouTube, 429 con `Retry-After`, apagado en dev/tests), validacion estricta, cabeceras de seguridad con CSP probada por E2E, auditoria de dependencias y modo produccion | RNF-07/RNF-09; el proxy de Vercel oculta la IP real, por eso la clave principal es el device id |
| 2026-10-03 | F12-GATE | Segundo plano + reproduccion inmediata: (A) `MediaSessionBridge` (metadata + play/pausa/next/prev/seek), `PlaybackResilience` (`visibilitychange`/`pageshow`, reanudar solo si el navegador pauso y el usuario no), PWA (`manifest.webmanifest`, service worker que nunca cachea `/api/*`, iconos generados con `scripts/generate_icons.py`); (B) `select` optimista que para el audio anterior al instante y marca la fila como cargando, cancelacion de peticiones obsoletas (`AbortController` + `aborted` silencioso), reutilizacion del iframe de YouTube (`loadVideoById`, sin recrear el player) y precarga de la siguiente pista local | `FEAT-005`; medicion E2E `instant-play`: clic->titulo ~115 ms (antes: esperaba el POST completo). Limite aceptado: el iframe de YouTube se pausa al bloquear el movil |
| 2026-10-03 | F13-GATE | Letras: `POST /api/lyrics` reconstruido (entidad `Lyrics`, puerto `LyricsProvider`, `LyricsService` con estrategia fuente-propia -> LRCLIB y cache TTL inclusivo de los fallos) + adapter `LrclibClient` (keyless, timeout 8 s) + 204 cuando no hay letras; UI en el reproductor (`LyricsPanel` HeroUI, cache por cancion, estados carga/vacio/error, texto como JSX) | `FEAT-004`; un fallo de letras nunca interrumpe la reproduccion. Backend: ruff/mypy/**401 tests**/94.3 % |
| 2026-10-03 | SEC-001-GATE | Rate limiting en proceso (ventana deslizante, clave device-id + IP), `MaxBodySizeMiddleware` (413), `SecurityHeadersMiddleware` (nosniff/frame/referrer/HSTS/Permissions-Policy/CSP de API), `TrustedHostMiddleware`, CORS con headers concretos, `X-Device-Id` con formato y longitud acotados, `max_length` en schemas, validacion de MP3/WAV + 100 MB en el frontend, timeout global del `httpx` compartido, versiones fijadas (`pyproject` + `uv.lock`), `pip-audit` y `npm audit` sin vulnerabilidades; CSP de la pagina en `vercel.json` ajustada a YouTube/Spotify | Auditoria de secretos: historial limpio, nada que rotar (el unico literal es el Client ID publico en este AGEND). Backend: 401 tests; frontend: lint/tsc/147 tests; E2E: 21 (20 desktop + 1 mobile) |
| 2026-10-03 | LATENCY-FIX | Velocidad percibida: (1) `POST /api/playlists/{id}/songs/batch` + `PlaylistService.add_songs` anaden N canciones con **una** lectura y **una** escritura (antes: N peticiones HTTP, cada una releyendo y reescribiendo la playlist entera) y el frontend usa el lote al agregar varias canciones de Spotify/YouTube/local; (2) el `apiClient` reintenta una vez las lecturas idempotentes (`GET`) en timeout / red / 502-503-504, con un primer plazo ampliado (`COLD_START_TIMEOUT_MS` = 20 s) para absorber el arranque en frio de Render, de modo que "despertar" el servidor ya no muestra el toast de timeout; las escrituras nunca reintentan | Feedback del usuario: error "el servidor tarda demasiado" al agregar musica de Spotify. Backend: ruff/mypy/**405**/94.3 %; frontend: lint/tsc/**152**; E2E 21; verificado en vivo (3 canciones -> 1 request, `size=3`) |

## ValidaciÃ³n de entrega de este AGEND.md

- [x] Contexto del proyecto
- [x] Nombre MigMusic
- [x] Requisitos originales del taller
- [x] Lista doblemente enlazada
- [x] Spotify Web API
- [x] Spotify Web Playback SDK
- [x] MÃºsica local
- [x] Backend Python
- [x] Frontend
- [x] Reproductor funcional
- [x] Adelantar segundos
- [x] F4: Layout, design tokens, componentes, API client, controladores
- [x] F5: AudioPlayer, LocalAudioPlayer, metadata ID3, IndexedDB, persistencia local
- [x] F6: OAuth PKCE + sesiÃ³n, catÃ¡logo Spotify (bÃºsqueda/playlists/guardadas), SpotifyPlayer con Web Playback SDK, errores manejados
- [x] F7: IntegraciÃ³n - seek/skip/cambio de fuente/fin de pista sincronizados entre backend, players y UI; lista didÃ¡ctica animada
- [x] F8: Favoritos con corazÃ³n, bÃºsqueda en la lista con find (Enter resalta el primer match), filtro de solo favoritas, repeat verificado y reordenar con drag & drop
- [x] F9: Pulido - contraste AA (tokens de texto por tema), accesibilidad (focus trap en diÃ¡logo, aria-current, group label, 44px), prefers-color-scheme, reduced-motion, responsive 4 breakpoints y code-splitting de metadata
- [x] F10: Adaptador SQL (Neon) + tests de contrato, render.yaml (blueprint), vercel.json (proxy de un solo origen), ADR-006 (plataformas verificadas) y docs de despliegue actualizadas â€” el despliegue real en las cuentas (Vercel/Render/Neon/Spotify) lo ejecuta el usuario con la checklist entregada
- [x] F11: Suite E2E Playwright (flujo maestro desktop + mÃ³vil, smoke y accesibilidad axe A/AA), fix del bug de arranque que encontrÃ³ el E2E, job `e2e` en CI, criterios de aceptaciÃ³n actualizados con evidencia y reporte final en `docs/testing.md` â€” quedan como acciÃ³n manual del usuario el despliegue en la nube y la demo con cuenta Spotify Premium
- [x] Retroceder segundos
- [x] DiseÃ±o animado
- [x] Responsive
- [x] Cloud deployment
- [x] Seguridad
- [x] Testing
- [x] Roadmap
- [x] Criterios de aceptaciÃ³n
- [x] Preguntas para el agente de desarrollo
- [x] IDs Ãºnicos para las preguntas
- [x] Estados de las preguntas
- [x] Orden de entrevista
- [x] Dependencias entre preguntas
- [x] Reglas para decisiones tÃ©cnicas
- [x] POO obligatoria y estructura por capas (requisito adicional)
- [x] Backend completamente en Python (requisito adicional)
