# AGEND.md — MigMusic

> **Fuente de verdad del proyecto MigMusic.**
> Este archivo es leído por el **agente de desarrollo**. No es documentación pasiva: es una guía operativa.
> El agente de desarrollo **debe entrevistar al usuario** (sección [Requirements Interview](#requirements-interview)), registrar las respuestas aquí mismo, y solo cuando se cumpla el [Implementation Gate](#implementation-gate) comenzar a programar.

- **Idioma de conversación con el usuario:** español.
- **Idioma del código:** inglés (ver [Restricciones globales](#restricciones-globales)).
- **Propietario del proyecto:** Miguel.
- **Versión del documento:** 1.2.0 (entrevista F0 completada y gate aprobado el 2026-09-28).

---

## 0. Cómo debe usar este archivo el agente de desarrollo

Orden obligatorio de lectura y actuación:

1. Leer este archivo completo, de arriba abajo.
2. Leer las skills listadas en [Índice de skills](#índice-de-skills). Empezar por `requirements-interview`, que gobierna la entrevista.
3. Ejecutar la entrevista **progresiva** (rondas de 4–6 preguntas, nunca todo de golpe).
4. Tras cada respuesta del usuario, **editar este archivo**: cambiar `Status`, rellenar `Answer` y `DecidedOn`, y añadir una línea al [Decision Log](#decision-log).
5. Cuando el [Implementation Gate](#implementation-gate) esté verde, implementar siguiendo el [Roadmap](#roadmap) y las skills técnicas.
6. Ante cualquier cambio de alcance posterior, volver a este archivo, actualizarlo y **solo entonces** cambiar el código.

Regla de oro: **si algo no está `CONFIRMED` aquí, el agente no lo asume.** Puede recomendarlo, pero debe preguntarlo.

---

## 1. Contexto del proyecto

**MigMusic** es un reproductor de música web completo. Nació como un **taller académico de estructuras de datos** cuyo núcleo es la **lista doblemente enlazada** aplicada a una lista de reproducción de canciones. El objetivo es convertir ese ejercicio en un producto real: con reproductor funcional, música de Spotify, música local del equipo del usuario, interfaz moderna y animada, diseño responsive y despliegue en la nube.

Dos dimensiones conviven y ambas son evaluables:

| Dimensión | Qué debe demostrar |
|---|---|
| **Académica** | Una lista doblemente enlazada **real** (nodos con `previous`/`next`), no un array disfrazado, explicable paso a paso. |
| **Producto** | Un reproductor web usable, bonito, seguro, probado y desplegado. |

## 2. Requisitos originales del taller (inmutables)

El taller solicita construir una aplicación usando el concepto de **LISTA DOBLEMENTE ENLAZADA** para simular y gestionar una lista de reproducción:

- [ ] Agregar una canción al inicio.
- [ ] Agregar una canción al final.
- [ ] Agregar una canción en cualquier posición.
- [ ] Eliminar una canción.
- [ ] Adelantar canción (siguiente).
- [ ] Retroceder canción (anterior).
- [ ] Interfaz frontend con la que el usuario interactúe.
- [ ] Otras funcionalidades adicionales pertinentes (mínimo 2, propuestas por el agente y elegidas por el usuario — ver `FEAT-*`).

> Estos requisitos **no pueden eliminarse ni degradarse** por ninguna decisión posterior.

## 3. Objetivo de MigMusic

Debe tener: reproductor funcional · playlist funcional · lista doblemente enlazada · música de Spotify · música local · interfaz moderna · animaciones · diseño responsive · controles de reproducción · adelantar segundos · retroceder segundos · agregar canciones · eliminar canciones · navegar entre canciones · despliegue en la nube.

## 4. Requisitos funcionales (RF)

| ID | Requisito | Origen |
|---|---|---|
| RF-01 | Play / Pause | Producto |
| RF-02 | Next / Previous (navegación por la lista doblemente enlazada) | Taller |
| RF-03 | **Skip forward N segundos** (N definido en `PLAYER-001`) | Producto |
| RF-04 | **Skip backward N segundos** (N definido en `PLAYER-002`) | Producto |
| RF-05 | Seek mediante barra de progreso | Producto |
| RF-06 | Volume y Mute | Producto |
| RF-07 | Agregar canción al inicio / al final / en posición arbitraria | Taller |
| RF-08 | Eliminar canción (por referencia y por posición) | Taller |
| RF-09 | Seleccionar canción de la lista y reproducirla | Producto |
| RF-10 | Fuente **Spotify** (Web API + Web Playback SDK) | Producto |
| RF-11 | Fuente **Música local** (File Picker, HTML5 Audio o alternativa adecuada) | Producto |
| RF-12 | Playlist unificada que puede contener canciones de ambas fuentes, respetando sus límites técnicos | Producto |
| RF-13 | ≥ 2 funcionalidades adicionales aprobadas por el usuario | Taller |
| RF-14 | Interfaz **funcional**, no mockup: todos los controles principales operan de verdad | Producto |

## 5. Requisitos no funcionales (RNF)

| ID | Requisito |
|---|---|
| RNF-01 | **POO** en todo el sistema (backend Python y frontend). Ver [Arquitectura](#8-arquitectura-objetivo). |
| RNF-02 | Estructura de carpetas **bien organizada y separada por capas/responsabilidades**, de modo que se note buena arquitectura. |
| RNF-03 | Backend **100 % Python**. Ninguna lógica de servidor en otro lenguaje. |
| RNF-04 | Código, comentarios técnicos, nombres y tipos **en inglés**. |
| RNF-05 | Responsive: desktop, laptop, tablet y mobile. |
| RNF-06 | Animaciones acordes al nivel decidido (`VIS-006`), respetando `prefers-reduced-motion`. |
| RNF-07 | Seguridad: secretos solo en variables de entorno; OAuth correcto; sin secretos en el frontend. |
| RNF-08 | Testing automatizado (unitario, integración, e2e mínimo). |
| RNF-09 | Desplegable en la nube con HTTPS, CORS, logs y configuración de producción. |
| RNF-10 | Accesibilidad básica (teclado, foco visible, ARIA en controles, contraste). |

## Restricciones globales

1. **Backend: Python obligatorio.** El framework (FastAPI / Flask / Django) se decide en `BACK-001`.
2. **Programación Orientada a Objetos** obligatoria: clases con responsabilidad única, encapsulación, abstracción mediante interfaces/clases abstractas, polimorfismo entre fuentes de audio, composición sobre herencia, inyección de dependencias.
3. **Código en inglés**: variables, funciones, clases, interfaces, tipos, componentes, métodos y comentarios técnicos.
4. **La lista doblemente enlazada no puede sustituirse por un array/list nativo** como estructura de la playlist activa.
5. **Spotify y música local son dos fuentes distintas.** El Web Playback SDK **no** reproduce archivos locales. Ver skill `spotify-integration` y `local-audio`.
6. **Ningún secreto** (Client Secret, tokens, claves) en el repositorio ni en el bundle del frontend.
7. **Estructura organizada y separada** (ver sección 8): cada capa en su carpeta, sin dependencias circulares, sin lógica de negocio en controladores/rutas ni en componentes de UI.

---

## 8. Arquitectura objetivo

> Esta arquitectura es la **hipótesis de trabajo** que el agente debe evaluar y ajustar con el usuario (`ARCH-*`, `BACK-*`, `FRONT-*`). Los principios (capas, POO, separación) **no son negociables**; los detalles sí.

### 8.1 Principios

- **Arquitectura por capas / hexagonal (ports & adapters):** el dominio no conoce frameworks, HTTP, Spotify ni base de datos.
- **Dependencias hacia adentro:** `api → application → domain`; `infrastructure → domain` (implementa puertos definidos en dominio/aplicación).
- **SOLID** aplicado explícitamente (y demostrable en revisión de código).
- **Inyección de dependencias** en el punto de composición (`container`/`main`), nunca `import` de implementaciones concretas dentro del dominio.
- **DTOs/Schemas** en el borde (API); las entidades de dominio nunca se serializan directamente.
- **Excepciones de dominio propias**, traducidas a respuestas HTTP en un único lugar.

### 8.2 Estructura de carpetas propuesta (monorepo)

```
migmusic/
├── AGEND.md
├── README.md
├── .env.example                      # solo nombres de variables, jamás valores reales
├── docker-compose.yml                # entorno local reproducible
├── docs/
│   ├── architecture.md               # diagramas y decisiones (ADR)
│   ├── adr/                          # Architecture Decision Records (uno por decisión)
│   ├── api.md
│   └── testing.md                    # estrategia de pruebas + reporte criterio → evidencia (F11)
├── skills/                           # skills para el agente (entregadas junto a este archivo)
├── backend/                          # 100 % Python
│   ├── pyproject.toml
│   ├── src/migmusic/
│   │   ├── main.py                   # composition root: crea app y cablea dependencias
│   │   ├── core/                     # transversal: config, logging, errores base, seguridad
│   │   │   ├── config.py             # Settings (lee variables de entorno)
│   │   │   ├── logging.py
│   │   │   └── exceptions.py
│   │   ├── domain/                   # REGLAS DE NEGOCIO PURAS (sin frameworks)
│   │   │   ├── entities/
│   │   │   │   ├── song.py           # Song (value object / entity)
│   │   │   │   ├── playlist.py       # Playlist (usa DoublyLinkedList)
│   │   │   │   └── audio_source.py   # enum AudioSourceType {LOCAL, SPOTIFY}
│   │   │   ├── structures/
│   │   │   │   ├── node.py           # Node
│   │   │   │   └── doubly_linked_list.py  # DoublyLinkedList
│   │   │   ├── ports/                # interfaces abstractas (ABC / Protocol)
│   │   │   │   ├── playlist_repository.py
│   │   │   │   ├── music_provider.py # contrato común para fuentes de música
│   │   │   │   └── token_store.py
│   │   │   └── exceptions.py         # EmptyPlaylistError, InvalidPositionError...
│   │   ├── application/              # CASOS DE USO (orquestan dominio + puertos)
│   │   │   ├── services/
│   │   │   │   ├── playlist_service.py
│   │   │   │   ├── playback_service.py
│   │   │   │   └── spotify_auth_service.py
│   │   │   └── dto/
│   │   ├── infrastructure/          # ADAPTADORES concretos
│   │   │   ├── spotify/
│   │   │   │   ├── spotify_client.py       # cliente HTTP a Spotify Web API
│   │   │   │   ├── spotify_oauth.py        # Authorization Code + PKCE, refresh
│   │   │   │   └── spotify_music_provider.py  # implementa MusicProvider
│   │   │   ├── persistence/
│   │   │   │   ├── in_memory_playlist_repository.py
│   │   │   │   └── sql_playlist_repository.py   # solo si se aprueba DB
│   │   │   └── security/
│   │   │       └── session_token_store.py
│   │   └── api/                      # CAPA DE ENTRADA (HTTP)
│   │       ├── routers/              # controladores delgados: sin lógica de negocio
│   │       ├── schemas/              # request/response models
│   │       ├── dependencies.py       # inyección de dependencias del framework
│   │       └── error_handlers.py     # excepciones de dominio → HTTP
│   └── tests/
│       ├── unit/                     # dominio y servicios (sin red, sin disco)
│       ├── integration/              # API + adaptadores (con dobles de Spotify)
│       └── conftest.py
├── frontend/                         # tecnología según FRONT-001
│   ├── package.json
│   ├── vercel.json                   # rewrite /api/* → Render (DEPLOY-002, un solo origen)
│   └── src/
│       ├── domain/                   # DoublyLinkedList (espejo, si se aprueba ARCH-001), Song, tipos
│       ├── players/                  # POO: AudioPlayer (abstracto), LocalAudioPlayer, SpotifyPlayer
│       ├── services/                 # ApiClient, PlaylistController, PlaybackController
│       ├── storage/                  # LocalLibraryRepository (IndexedDB) si se aprueba
│       ├── ui/
│       │   ├── components/           # presentacionales, sin lógica de negocio
│       │   ├── layouts/
│       │   └── animations/
│       ├── styles/                   # design tokens (colores, espaciado, motion)
│       └── main.*
└── render.yaml                       # IaC: blueprint de Render (DEPLOY-001)
```

### 8.3 Clases centrales (nombres de referencia)

| Clase | Capa | Responsabilidad única |
|---|---|---|
| `Node` | domain | Contener `song`, `previous`, `next`. |
| `DoublyLinkedList` | domain | Operaciones estructurales de la lista y puntero `current`. |
| `Song` | domain | Datos inmutables de una canción y su `AudioSourceType`. |
| `Playlist` | domain | Nombre + `DoublyLinkedList`; reglas propias (duplicados, modos repeat/shuffle si se aprueban). |
| `MusicProvider` (ABC) | domain/ports | Contrato de una fuente de música (búsqueda, resolución de reproducción). |
| `SpotifyMusicProvider` | infrastructure | Implementa `MusicProvider` con Spotify Web API. |
| `PlaylistRepository` (ABC) | domain/ports | Persistir/recuperar playlists. |
| `PlaylistService` | application | Casos de uso: crear, añadir, insertar, eliminar, mover. |
| `PlaybackService` | application | Casos de uso: next, previous, seek, skip N segundos (estado de reproducción). |
| `SpotifyAuthService` | application | Flujo OAuth, refresh de tokens, cierre de sesión. |
| `AudioPlayer` (abstracta, frontend) | frontend/players | `play/pause/seek/setVolume/onEnded...` |
| `LocalAudioPlayer` / `SpotifyPlayer` | frontend/players | Polimorfismo: misma interfaz, distinto motor. |

### 8.4 Patrones esperados (justificar en ADR si se cambian)

Strategy (fuentes de audio) · Repository (persistencia) · Factory (creación de players/providers) · Adapter (Spotify) · Observer/Event emitter (estado del player → UI) · Dependency Injection (composition root).

### 8.5 Dónde vive la lista doblemente enlazada (decisión crítica → `ARCH-001`)

El reproductor de música local corre **en el navegador**; los archivos locales no deben viajar al servidor salvo decisión explícita. El backend es Python. Hay tensión que el agente debe resolver con el usuario:

- **Opción A — DLL solo en backend (Python):** máxima pureza académica en Python, pero cada Next/Previous implica red; incómodo con archivos locales.
- **Opción B — DLL solo en frontend:** respuesta inmediata, pero el backend Python queda reducido a OAuth/persistencia y pierde peso académico.
- **Opción C — DLL en ambos con contrato compartido (recomendada como hipótesis):** el backend Python es la fuente de verdad de playlists persistidas y expone la API; el frontend mantiene una implementación equivalente para navegación instantánea; ambas se validan con **los mismos casos de prueba (fixtures de contrato)**. Costo: duplicación controlada y disciplina de sincronización.

El agente debe explicar esto, recomendar y **preguntar**; no asumir.

---

## 9. Lista doblemente enlazada — especificación

Estructura mínima:

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

Operaciones mínimas (nombres en inglés; adaptar al estilo del lenguaje, ej. `snake_case` en Python):

`insertAtBeginning()` · `insertAtEnd()` · `insertAt()` · `remove()` · `removeAt()` · `find()` · `moveNext()` · `movePrevious()` · `getCurrent()` · `getSize()` · `clear()`

Reglas:

- Implementación **real** con nodos enlazados. Prohibido usar `list`/`Array` como almacenamiento interno de la estructura.
- Mantener invariantes: `head.previous is None`, `tail.next is None`, `size` coherente, `current` válido o `None`.
- Casos borde obligatorios: lista vacía, un solo elemento, inserción/eliminación en extremos, posición fuera de rango, eliminar el nodo `current`, `moveNext` en `tail`, `movePrevious` en `head`.
- Decisión pendiente: comportamiento en extremos (¿se detiene o es circular?) → `PLAYLIST-009`.
- El agente debe poder **explicar al usuario cómo la lista se usa dentro de la playlist** (skill `doubly-linked-list` incluye guion de explicación).
- Complejidad documentada por operación (ej. `insertAtBeginning` O(1), `insertAt` O(n)).

## 10. Spotify

MigMusic usa **Spotify Web API** y **Spotify Web Playback SDK**. Debe documentarse y respetarse:

- **OAuth** con *Authorization Code Flow* (con PKCE cuando el cliente lo requiera). No usar Implicit Grant (obsoleto).
- **Tokens:** access token de vida corta + refresh token; **el Client Secret jamás sale del backend**.
- **Scopes** mínimos necesarios (el agente los lista y justifica en `SPOTIFY-*`).
- **Redirect URI:** debe coincidir exactamente con la registrada en el Spotify Dashboard; las reglas de HTTPS/loopback **deben verificarse en la documentación vigente** antes de configurar.
- **Client ID / Client Secret / variables de entorno:** solo por `.env` local (ignorado por git) y variables del proveedor cloud.
- **Requisitos de cuenta:** el Web Playback SDK exige cuenta **Spotify Premium**; verificar limitaciones actuales de modo desarrollo (usuarios permitidos, cuotas) y de navegadores/móviles soportados.
- **Manejo de errores:** 401 (token expirado → refresh), 403, 429 (respetar `Retry-After`), errores del SDK (`initialization_error`, `authentication_error`, `account_error`, `playback_error`).
- **Sesiones y expiración:** cookie de sesión `HttpOnly`, `Secure`, `SameSite` adecuada; refresh transparente.
- **Separación de fuentes:** el SDK reproduce solo contenido de Spotify. **Nunca** intentar reproducir archivos locales con él.

> El agente **debe consultar la documentación oficial vigente de Spotify** antes de implementar (las políticas de acceso y endpoints cambian con el tiempo) y registrar en un ADR cualquier limitación encontrada.

Detalle operativo: skill `spotify-integration`.

## 11. Música local

- Selección con **File Picker**; **drag and drop** si se aprueba (`LOCAL-003`).
- Formatos: MP3, WAV y otros compatibles con el navegador (lista final en `LOCAL-001`; el agente debe advertir diferencias de soporte entre navegadores).
- Reproducción con **HTML5 Audio API** (o alternativa técnicamente adecuada, ej. Web Audio API si se aprueba visualizador/ecualizador).
- Debe poder: reproducir, pausar, avanzar, retroceder, seek, cambiar canción, eliminar canción.
- Persistencia tras cerrar el navegador: implica almacenar blobs (IndexedDB) o solo metadatos con re-selección de archivos → **explicar implicaciones** (`LOCAL-006`, `LOCAL-008`).
- Gestión de memoria: liberar `URL.createObjectURL` con `revokeObjectURL`.
- Privacidad: por defecto, los archivos locales **no se suben** al servidor.

Detalle operativo: skill `local-audio`.

## 12. Seguridad

- Secretos solo en variables de entorno; `.env` en `.gitignore`; `.env.example` sin valores.
- Client Secret y refresh tokens solo en backend; sesión por cookie `HttpOnly`.
- Validar `state` en OAuth (anti-CSRF) y usar PKCE.
- CORS restrictivo (orígenes explícitos, nunca `*` con credenciales).
- Validación de entrada con schemas; límites de tamaño y tipo para cualquier subida.
- Cabeceras de seguridad (CSP compatible con el SDK de Spotify, HSTS en producción).
- Dependencias fijadas y auditadas; logs **sin** tokens ni datos sensibles.
- Rate limiting básico en endpoints de autenticación.

## 13. Testing

- **Unit (obligatorio, alta cobertura en dominio):** `DoublyLinkedList`, `Playlist`, servicios.
- **Integración:** rutas API con dobles de Spotify (sin llamar a Spotify real en CI).
- **Contrato DLL:** mismos casos en Python y en frontend si aplica `ARCH-001 = C`.
- **Frontend:** pruebas de componentes/controladores y de los players con dobles.
- **E2E mínimo:** flujo agregar → reproducir → next → previous → skip N seg → eliminar.
- **Manual guiado:** checklist responsive y Spotify real (requiere cuenta Premium).
- Herramientas concretas: `TEST-001`.

Detalle operativo: skill `testing-quality`.

## 14. Despliegue

Debe contemplarse: frontend, backend, HTTPS, variables de entorno, Spotify OAuth, CORS, Redirect URI de producción, logs y configuración de producción. Plataforma y topología: `DEPLOY-*`. Detalle operativo: skill `deployment-cloud`.

---

## Índice de skills

Ubicación: carpeta `skills/<nombre>/SKILL.md`. Cada una tiene **una responsabilidad concreta**.

| Skill | Responsabilidad | Cuándo se activa |
|---|---|---|
| `requirements-interview` | Conducir la entrevista progresiva, registrar respuestas, controlar el gate. | **Siempre primero.** |
| `backend-architecture-python` | Estructura por capas, POO, SOLID y reglas de organización del backend Python. | Al iniciar implementación backend y en cada revisión. |
| `doubly-linked-list` | Implementar, probar y explicar la lista doblemente enlazada. | Al implementar la playlist. |
| `spotify-integration` | OAuth, tokens, Web API, Web Playback SDK, errores. | Tras `SPOTIFY-*` confirmadas. |
| `local-audio` | Audio local, metadata, persistencia, formatos. | Tras `LOCAL-*` confirmadas. |
| `ui-ux-design` | Diseño visual, animaciones, responsive, accesibilidad, frontend POO. | Tras `VIS-*`, `UX-*`, `FRONT-*` confirmadas. |
| `testing-quality` | Estrategia y ejecución de pruebas, criterios de calidad. | Continuamente y antes de cada entrega. |
| `deployment-cloud` | Despliegue, HTTPS, CORS, entornos, logs. | Tras `DEPLOY-*` confirmadas. |

---

## Sistema de estados

| Estado | Significado | Acción del agente |
|---|---|---|
| `PENDING` | Aún no preguntada o sin respuesta. | Preguntar (cuando le toque por orden y dependencias). |
| `PROPOSED` | El agente propuso una opción/recomendación y espera confirmación. | No implementar; pedir confirmación. |
| `CONFIRMED` | El usuario decidió; respuesta registrada. | Usar como requisito firme. No volver a preguntar. |
| `REJECTED` | El usuario descartó la opción/funcionalidad. | No implementar; no volver a proponer salvo que el usuario lo pida. |

Transiciones válidas: `PENDING → PROPOSED → CONFIRMED | REJECTED`, `PENDING → CONFIRMED | REJECTED`, y `CONFIRMED → PENDING` únicamente si el usuario quiere **reabrir** la decisión (registrar en Decision Log).

Cada pregunta tiene: `Status`, `Priority` (`CRITICAL` bloquea el gate / `NORMAL` no), `DependsOn`, `Question`, `Guidance` (qué explicar/alternativas), `FollowUps` (preguntas adicionales condicionales), `Answer`, `DecidedOn`.

Al confirmar, el agente escribe por ejemplo:

```yaml
VIS-001:
  Status: CONFIRMED
  Answer: "Glassmorphism oscuro con acentos neón"
  DecidedOn: 2026-10-01
```

---

## Requirements Interview

### Reglas de la entrevista (resumen; el detalle está en la skill `requirements-interview`)

1. **Progresiva:** rondas temáticas de **4–6 preguntas**. Anunciar la ronda ("Vamos a definir el diseño visual de MigMusic."), preguntar, esperar respuesta, registrar, y pasar a la siguiente.
2. **Nunca** preguntar todo de una vez ni repetir preguntas `CONFIRMED`/`REJECTED`.
3. Respetar `DependsOn`: no preguntar una pregunta si sus dependencias siguen `PENDING`, salvo dependencia técnica que justifique alterar el orden (explicarlo).
4. Si una respuesta abre una decisión nueva, **crear** la pregunta adicional (ID nuevo con sufijo, ej. `LOCAL-006a`) en `PENDING` y hacerla en la misma ronda o la siguiente.
5. Para decisiones técnicas: explicar opciones, ventajas/desventajas, **recomendar**, preguntar y registrar. No asumir.
6. Si el usuario dice "no sé / lo que recomiendes": pasar a `PROPOSED` con la recomendación, pedir un "sí" explícito y entonces `CONFIRMED`.
7. Usar lenguaje claro; el usuario tiene interés en computación y redes y prefiere explicaciones **profundas y conceptuales**: cuando una decisión tenga consecuencias técnicas, explicar el porqué, no solo el qué.

### Orden recomendado de rondas

| Ronda | Tema | Prefijo | Depende de |
|---|---|---|---|
| R1 | Restricciones del proyecto | `CONS` | — |
| R2 | Diseño visual | `VIS` | R1 |
| R3 | UX | `UX` | R2 |
| R4 | Reproductor (core) | `PLAYER` | R1 |
| R5 | Playlist | `PLAYLIST` | R4 |
| R6 | Música local | `LOCAL` | R4, R5 |
| R7 | Spotify | `SPOTIFY` | R4, R5 |
| R8 | Frontend | `FRONT` | R2, R3, R6, R7 |
| R9 | Backend | `BACK` | R5, R7 |
| R10 | Base de datos | `DB` | R5, R6, R9 |
| R11 | Funcionalidades adicionales | `FEAT` | R4–R10 |
| R12 | Despliegue | `DEPLOY` | R8, R9, R10 |
| R13 | Testing | `TEST` | R8, R9 |

Transversal: `ARCH` (arquitectura) se plantea en **R5** y se afina en **R8–R9** porque depende de dónde vive la lista y de la persistencia.

**Dependencias técnicas que autorizan alterar el orden (ejemplos):**
- `SPOTIFY-004` (entorno de despliegue/Redirect URI) depende de `DEPLOY-001`.
- `FRONT-001` (tecnología) puede adelantarse si `VIS-*`/`FEAT-*` exigen capacidades concretas (ej. visualizador con Web Audio).
- `DB-001` depende de `LOCAL-006` (persistencia local) y `PLAYLIST-001` (múltiples playlists).
- `FEAT-*` de Web Audio (ecualizador/visualizador) modifica `LOCAL-*` y `SPOTIFY-*` (el SDK **no** expone audio para análisis; explicarlo).

---

### R1 — Project Constraints Questions

```yaml
CONS-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: []
  Question: "¿Este proyecto se entrega y evalúa como trabajo académico (con sustentación de la lista doblemente enlazada) además de ser un producto real? ¿Hay fecha límite?"
  Guidance: "Define el peso de la parte académica (documentación, explicabilidad) y el plazo, que condiciona el alcance del roadmap."
  Answer: "Trabajo académico + producto real. Fecha límite: 2026-10-02"
  DecidedOn: 2026-09-28

CONS-001a:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "Con 4 días hasta el 02/10, ¿qué nivel de alcance aceptas?"
  Guidance: "A: alcance completo recomendado. B: sin Spotify. C: todo el alcance con riesgo de no cerrar."
  Answer: "A - alcance completo recomendado; FEAT reducidas a 4 de bajo coste; sin visualizador/waveform/ecualizador/queue/velocidad/atajos"
  DecidedOn: 2026-09-28

CONS-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "¿Trabajarás solo o en equipo? ¿Cuál es tu nivel con Python, POO y el frontend que elijamos?"
  Guidance: "Ajusta la profundidad de explicaciones, comentarios y nivel de abstracción."
  Answer: "Trabajo en solo. Nivel técnico: ver CONS-002a"
  DecidedOn: 2026-09-28

CONS-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "¿Qué entorno de desarrollo usas (sistema operativo, editor, versión de Python/Node instaladas, Docker disponible)?"
  Guidance: "Determina scripts de arranque, Docker Compose y versiones mínimas."
  Answer: "Windows, VS Code, Python 3.11/3.13, Node 26, npm 11, Git 2.55, sin Docker"
  DecidedOn: 2026-09-28

CONS-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "¿Tienes o puedes crear una cuenta de Spotify Premium para probar el Web Playback SDK? ¿Quién más necesitará probar (usuarios de prueba)?"
  Guidance: "El SDK requiere Premium y el modo desarrollo de Spotify limita usuarios. Puede cambiar el alcance de la demo."
  Answer: "Cuenta Spotify Premium disponible"
  DecidedOn: 2026-09-28

CONS-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "¿Hay presupuesto para la nube (gratis únicamente, o puedes pagar algo)? ¿Tienes dominio propio?"
  Guidance: "Condiciona la plataforma de despliegue y HTTPS."
  Answer: "Solo planes gratuitos en nube y herramientas"
  DecidedOn: 2026-09-28

CONS-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: []
  Question: "¿Qué idioma debe tener la interfaz de usuario de MigMusic (español, inglés o ambos)?"
  Guidance: "El código va en inglés siempre; esto se refiere solo a los textos visibles. Si son ambos, planificar i18n."
  Answer: "Interfaz bilingüe: español + inglés (i18n por diccionario de claves)"
  DecidedOn: 2026-09-28

CONS-002a:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [CONS-002]
  Question: "¿Cuál es tu nivel con Python, POO y frontend?"
  Guidance: "Ajusta profundidad de explicaciones y comentarios. Se pregunta en la fase de pulido (F9)."
  Answer: null
  DecidedOn: null
```

### R2 — Visual Design Questions

```yaml
VIS-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "¿Qué estilo visual quieres para MigMusic? (moderno, futurista, minimalista, neón, glassmorphism, retro, oscuro tipo reproductor musical, otro)"
  Guidance: "Ofrecer 2–3 combinaciones concretas con una breve descripción de cómo se vería cada una."
  Answer: "D - Retro/vinilo"
  DecidedOn: 2026-09-28

VIS-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-001]
  Question: "¿Prefieres tema oscuro, claro o ambos (con selector)?"
  Guidance: "Ambos implica design tokens con dos paletas y mayor esfuerzo de pruebas de contraste."
  Answer: "Ambos temas con selector"
  DecidedOn: 2026-09-28

VIS-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-001]
  Question: "¿Qué colores principales quieres?"
  Guidance: "Aceptar nombres, hex o una referencia (una app, una imagen). Validar contraste accesible."
  Answer: "Azul marino / eléctrico + negro; acentos a cargo del agente"
  DecidedOn: 2026-09-28

VIS-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-003]
  Question: "¿Qué colores secundarios / de acento quieres?"
  Guidance: "Proponer una paleta derivada si no tiene preferencia."
  Answer: "Primario #1E6BFF, acento #4338CA, fondo #0A0D14 (opción i, sobria)"
  DecidedOn: 2026-09-28

VIS-005:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [VIS-003]
  Question: "¿Quieres usar gradientes? ¿Fijos o que cambien según la portada de la canción?"
  Guidance: "Gradientes dinámicos por portada requieren extraer color dominante (costo técnico moderado)."
  Answer: "Sin gradientes (propuesta de paleta anterior rechazada)"
  DecidedOn: 2026-09-28

VIS-006:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-001]
  Question: "¿Qué tan intensas quieres las animaciones: sutiles, moderadas o muy animadas?"
  Guidance: "Explicar impacto en rendimiento móvil y en accesibilidad (prefers-reduced-motion)."
  Answer: "Sutiles, respetando prefers-reduced-motion"
  DecidedOn: 2026-09-28

VIS-007:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "¿Quieres un visualizador de audio?"
  Guidance: "Con música local es viable (Web Audio API AnalyserNode). Con Spotify SDK NO se puede analizar el audio: advertir. Puede simularse visualmente (no real) — explicar la diferencia honestamente."
  FollowUps: ["Si sí: crear FEAT-* de visualizador y revisar LOCAL-* (Web Audio)."]
  Answer: "No aplica por CONS-001a (sin visualizador)"
  DecidedOn: 2026-09-28

VIS-008:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [VIS-007]
  Question: "¿Quieres ondas de audio (waveform) en la barra de progreso?"
  Guidance: "Waveform real requiere decodificar el archivo local; para Spotify no está disponible."
  Answer: "No aplica por CONS-001a (sin waveform)"
  DecidedOn: 2026-09-28

VIS-009:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "¿Quieres animaciones en la portada de la canción (giro tipo vinilo, pulso, parallax)?"
  Guidance: "Mostrar opciones con una descripción visual."
  Answer: "Solo microinteracciones sutiles en CSS puro: pulso suave en la portada al reproducir, sin giro tipo vinilo ni parallax"
  DecidedOn: 2026-09-28

VIS-010:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "¿Quieres efectos visuales cuando cambia la canción (transición de portada, cambio de fondo, etc.)?"
  Guidance: "Vincular con VIS-005 si hay gradientes dinámicos."
  Answer: "Cross-fade de portada y titulo al cambiar de cancion, en CSS puro (transform/opacity)"
  DecidedOn: 2026-09-28

VIS-011:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "¿Quieres microinteracciones en botones y controles (hover, ripple, rebote al pulsar)?"
  Guidance: "Bajo costo, alto efecto percibido."
  Answer: "Si - hover, ripple y foco visibles en botones y controles, con prefers-reduced-motion respetado"
  DecidedOn: 2026-09-28

VIS-012:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-001]
  Question: "¿Cómo quieres distribuir la interfaz? (sidebar, barra inferior, reproductor central, layout tipo dashboard, otro)"
  Guidance: "Mostrar un esquema ASCII de cada opción y cómo se adapta a mobile."
  Answer: "B - Reproductor central + lista debajo"
  DecidedOn: 2026-09-28
```

### R3 — UX Questions

```yaml
UX-001:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-012]
  Question: "¿Cómo quieres que se vea la lista de canciones: filas con portada, tarjetas, tabla compacta?"
  Guidance: "Debe permitir ver qué nodo es el actual y, opcionalmente, una visualización didáctica de los nodos enlazados."
  Answer: "A - filas con portada pequeña y duración"
  DecidedOn: 2026-09-28

UX-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "¿Quieres una vista didáctica que muestre la lista doblemente enlazada (nodos y flechas prev/next) en tiempo real? ¿Siempre visible o en un panel opcional?"
  Guidance: "Muy valiosa para sustentación académica. Recomendarla si CONS-001 indica evaluación."
  Answer: "B - vista didáctica de nodos alternable con botón"
  DecidedOn: 2026-09-28

UX-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-012]
  Question: "¿Cómo quieres agregar canciones: botón + modal, panel lateral, arrastrando archivos, buscador de Spotify integrado?"
  Guidance: "Debe cubrir inicio, final y posición arbitraria de forma comprensible."
  Answer: "A - botón + modal con pestañas Local/Spotify y selector de posición"
  DecidedOn: 2026-09-28

UX-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-012]
  Question: "¿Cómo deben comportarse los mensajes de error/estado (toasts, banners, diálogos) y qué debe ver el usuario si Spotify no está conectado?"
  Guidance: "Definir estados vacíos, cargando, error y sin conexión."
  Answer: "A - toasts + pantalla vacía ilustrada sin Spotify conectado"
  DecidedOn: 2026-09-28
```

### R4 — Player Questions

```yaml
PLAYER-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "¿Cuántos segundos debe adelantar el botón de avance?"
  Guidance: "Sugerir 10 s como valor habitual; permitir configurable si el usuario lo desea."
  Answer: "5 segundos"
  DecidedOn: 2026-09-28

PLAYER-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYER-001]
  Question: "¿Cuántos segundos debe retroceder el botón de retroceso?"
  Guidance: "Puede ser igual o distinto al avance."
  Answer: "5 segundos"
  DecidedOn: 2026-09-28

PLAYER-002a:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-002]
  Question: "Retroceso de 5 s: si la posición es <= 5 s, ¿ir a la pista anterior o quedarse en 0:00?"
  Guidance: "A es el comportamiento estándar y evita el conflicto con Previous."
  Answer: "A - si posicion <= 5 s -> pista anterior; si no -> retroceder 5 s"
  DecidedOn: 2026-09-28

PLAYER-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "¿Quieres reproducción automática de la siguiente canción al terminar la actual?"
  Guidance: "Se implementa con el evento de fin de pista + moveNext() de la lista."
  Answer: "A - autoplay a la siguiente (moveNext)"
  DecidedOn: 2026-09-28

PLAYER-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-003]
  Question: "¿Quieres reproducción aleatoria (shuffle)?"
  Guidance: "Explicar que shuffle sobre una lista enlazada exige una estrategia (permutación de índices o reordenar nodos) y cómo afecta a 'anterior'."
  FollowUps: ["Si sí: crear PLAYLIST-* sobre cómo se conserva el historial para Previous."]
  Answer: "Sí, estrategia (b): lista intacta + índice de orden de reproducción"
  DecidedOn: 2026-09-28

PLAYER-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-003]
  Question: "¿Quieres repetir una canción?"
  Guidance: "Modo 'repeat one'."
  Answer: "Sí (repeat one), vía FEAT-001-d"
  DecidedOn: 2026-09-28

PLAYER-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYER-003, PLAYLIST-009]
  Question: "¿Quieres repetir toda la playlist?"
  Guidance: "Relacionado con si la lista se comporta como circular al llegar a los extremos."
  Answer: "Sí (repeat all como modo en el servicio), vía FEAT-001-d"
  DecidedOn: 2026-09-28

PLAYER-007:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-001]
  Question: "¿Quieres una barra de progreso interactiva (click y arrastre para hacer seek)?"
  Guidance: "Recomendado; es parte del requisito de seek."
  Answer: "Sí - barra de progreso interactiva (click y arrastre)"
  DecidedOn: 2026-09-28

PLAYER-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "¿Quieres control de volumen (slider) y mute?"
  Guidance: "Recomendado. Explicar que en algunos móviles el volumen lo controla el sistema."
  Answer: "Sí - slider de volumen y mute"
  DecidedOn: 2026-09-28

PLAYER-009:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "¿Quieres control de velocidad de reproducción?"
  Guidance: "Viable en audio local (playbackRate). El Web Playback SDK de Spotify no ofrece control de velocidad: advertir."
  Answer: "No aplica por CONS-001a (sin control de velocidad)"
  DecidedOn: 2026-09-28

PLAYER-010:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [CONS-001]
  Question: "¿Quieres atajos de teclado? Si sí, ¿cuáles (espacio = play/pausa, flechas = skip, etc.)?"
  Guidance: "Cuidar accesibilidad y no interferir con campos de texto."
  Answer: "No aplica por FEAT-001-a rechazada (sin atajos de teclado)"
  DecidedOn: 2026-09-28

PLAYER-011:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [ARCH-001, PLAYER-002a]
  Question: "¿Dónde vive el estado de reproducción (posición actual, seek y skip de 5 s)?"
  Guidance: "Con ARCH-001=A la lista vive en el backend, pero el audio suena en el navegador. Afecta a cómo se prueba PLAYER-002a."
  Answer: "Backend decide y frontend ejecuta: PlaybackService guarda pista, modos y posicion; el frontend reporta su posicion y envia skip"
  DecidedOn: 2026-09-28
```

### R5 — Playlist Questions

```yaml
PLAYLIST-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYER-003]
  Question: "¿Quieres una única playlist o múltiples playlists?"
  Guidance: "Múltiples playlists = una DoublyLinkedList por playlist; impacta en persistencia y UI."
  Answer: "B - varias playlists con persistencia en Postgres"
  DecidedOn: 2026-09-28

PLAYLIST-001a:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [PLAYLIST-001, DB-001]
  Question: "Si Neon (Postgres gratuito) falla o se agota, ¿qué plan degradado aceptas?"
  Guidance: "Opciones: (a) solo lectura con aviso, (b) reiniciar en memoria y avisar, (c) exportar/importar JSON. Se pregunta antes de F10."
  Answer: null
  DecidedOn: null

PLAYLIST-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres poder crear playlists nuevas?"
  Guidance: "Solo aplica si hay múltiples."
  Answer: "Sí - crear playlists (PlaylistService.create)"
  DecidedOn: 2026-09-28

PLAYLIST-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres renombrar playlists?"
  Guidance: "Solo aplica si hay múltiples."
  Answer: "Sí - renombrar (PlaylistService.rename)"
  DecidedOn: 2026-09-28

PLAYLIST-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres reordenar canciones mediante drag and drop?"
  Guidance: "Explicar que se traduce en removeAt + insertAt (o reenlazado de nodos) y qué costo tiene O(n)."
  Answer: "Sí, vía FEAT-001-e (drag and drop)"
  DecidedOn: 2026-09-28

PLAYLIST-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres favoritos?"
  Guidance: "Puede ser una marca en Song o una playlist especial."
  Answer: "Sí, vía FEAT-001-b (favoritos)"
  DecidedOn: 2026-09-28

PLAYLIST-006:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [PLAYER-003]
  Question: "¿Quieres historial de reproducción?"
  Guidance: "Distinto de 'anterior' de la lista; explicar diferencia."
  Answer: null
  DecidedOn: null

PLAYLIST-007:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres una cola de reproducción (queue) independiente de la playlist?"
  Guidance: "La cola es una estructura distinta (posible uso de Queue); aclarar que no sustituye la lista doblemente enlazada."
  Answer: "No aplica por CONS-001a (sin queue)"
  DecidedOn: 2026-09-28

PLAYLIST-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres búsqueda dentro de la playlist?"
  Guidance: "Usa find(); mencionar O(n)."
  Answer: "Sí, vía FEAT-001-c (búsqueda con find)"
  DecidedOn: 2026-09-28

PLAYLIST-009:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYER-003]
  Question: "Al llegar al final (o al inicio) de la lista, ¿debe detenerse o dar la vuelta (comportamiento circular)?"
  Guidance: "Circular implica enlazar tail↔head o simularlo en la capa de servicio. Explicar cuál conserva mejor el concepto puro de lista doblemente enlazada."
  Answer: "A - detenerse en los extremos (tail.next = None)"
  DecidedOn: 2026-09-28

PLAYLIST-009a:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-009]
  Question: "¿Cómo señala DoublyLinkedList que llegó al extremo: excepción o valor de retorno?"
  Guidance: "SKILL2 admite ambas; documentar la elegida."
  Answer: "Retorna bool (True = se movió); current no cambia en el extremo. Sin excepción"
  DecidedOn: 2026-09-28

PLAYLIST-009b:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-009]
  Question: "Al eliminar el nodo que está en current, ¿a dónde pasa current?"
  Guidance: "Afecta a lo que se reproduce tras borrar desde la UI."
  Answer: "Al siguiente; si era tail, al anterior; si era el único, current = None"
  DecidedOn: 2026-09-28

PLAYLIST-010:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [LOCAL-001, SPOTIFY-001]
  Question: "¿Puede una misma playlist mezclar canciones locales y de Spotify?"
  Guidance: "Técnicamente posible con dos motores (Strategy), pero implica cambio de player entre pistas; explicar posibles saltos/latencia y pérdida de gapless."
  Answer: null
  DecidedOn: null

ARCH-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Dónde debe vivir la lista doblemente enlazada: solo backend Python, solo frontend, o en ambos con contrato de pruebas compartido?"
  Guidance: "Ver sección 8.5 de AGEND.md. Explicar A/B/C con ventajas y desventajas y recomendar."
  Answer: "A - DLL solo en backend Python (tramo inicial de C)"
  DecidedOn: 2026-09-28

ARCH-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [ARCH-001]
  Question: "¿Aceptas la arquitectura por capas/hexagonal propuesta (domain / application / infrastructure / api) con inyección de dependencias? ¿Quieres ajustar algo de la estructura de carpetas?"
  Guidance: "Mostrar el árbol de la sección 8.2 y justificar cada carpeta. La separación y la POO no son negociables; los nombres sí."
  Answer: "Sí - arquitectura hexagonal por capas con DI y árbol 8.2"
  DecidedOn: 2026-09-28

ARCH-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [ARCH-002]
  Question: "¿Quieres documentar las decisiones como ADRs en docs/adr y diagramas (UML/Mermaid) de clases y secuencia?"
  Guidance: "Refuerza la evidencia de buena arquitectura, útil para sustentación."
  Answer: "Sí - ADRs en docs/adr y diagramas Mermaid"
  DecidedOn: 2026-09-28
```

### R6 — Local Music Questions

```yaml
LOCAL-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Qué formatos de audio quieres admitir (MP3, WAV, OGG, FLAC, AAC/M4A, otros)?"
  Guidance: "Explicar soporte real por navegador (ej. FLAC/OGG varían) y la validación por MIME y extensión."
  Answer: "A - MP3 y WAV (validación por MIME y extensión)"
  DecidedOn: 2026-09-28

LOCAL-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-001]
  Question: "¿Quieres permitir seleccionar múltiples archivos a la vez?"
  Guidance: "Atributo multiple del input; definir en qué orden entran a la lista (inicio/final)."
  Answer: "Sí - selección múltiple; entra al final de la lista"
  DecidedOn: 2026-09-28

LOCAL-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-002]
  Question: "¿Quieres drag and drop de archivos sobre la aplicación?"
  Guidance: "Complementa el File Picker; no lo reemplaza (accesibilidad y móvil)."
  Answer: "Sí - drag and drop además del File Picker"
  DecidedOn: 2026-09-28

LOCAL-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-001]
  Question: "¿Quieres obtener automáticamente metadata de los archivos (título, artista, álbum, duración)?"
  Guidance: "Se puede leer en el navegador con una librería de tags ID3; alternativa: procesar en backend Python (mutagen), pero implicaría subir el archivo. Explicar la implicación de privacidad."
  Answer: "A - tags ID3 en el navegador (sin subir archivos)"
  DecidedOn: 2026-09-28

LOCAL-005:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [LOCAL-004]
  Question: "¿Quieres mostrar la portada extraída de la metadata?"
  Guidance: "Definir portada por defecto cuando no exista."
  Answer: null
  DecidedOn: null

LOCAL-006:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [LOCAL-001]
  Question: "¿Quieres que la música local persista después de cerrar el navegador?"
  Guidance: "Explicar: (a) no persistir (simple, se pierde), (b) guardar solo metadatos y pedir re-seleccionar archivos, (c) guardar los blobs en IndexedDB (persistente pero ocupa disco del navegador y tiene cuotas). Recomendar según el caso."
  FollowUps: ["Si (c): confirmar LOCAL-008 y límites de espacio."]
  Answer: "B - solo metadatos; al volver se re-seleccionan los archivos"
  DecidedOn: 2026-09-28

LOCAL-006a:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [LOCAL-006]
  Question: "¿Cómo marca la UI los temas cuyo archivo local necesita re-selección?"
  Guidance: "Propuesta: borde ámbar + badge 'archivo perdido' + acción de re-selección. Se pregunta en F5."
  Answer: null
  DecidedOn: null

LOCAL-007:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [PLAYLIST-001]
  Question: "¿Quieres guardar las playlists localmente (en el navegador)?"
  Guidance: "Diferenciar de la persistencia en servidor (DB-001)."
  Answer: "Sí - playlists también en el navegador"
  DecidedOn: 2026-09-28

LOCAL-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [LOCAL-006, LOCAL-007]
  Question: "¿Qué estrategia de almacenamiento local prefieres (IndexedDB, localStorage, File System Access API, ninguna)?"
  Guidance: "localStorage no sirve para blobs; File System Access API no está en todos los navegadores. Explicar y recomendar (normalmente IndexedDB)."
  Answer: "A - IndexedDB (gratis; ninguna opción de pago)"
  DecidedOn: 2026-09-28
```

### R7 — Spotify Questions

```yaml
SPOTIFY-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-004]
  Question: "¿Ya tienes creada una app en el Spotify Developer Dashboard? Si no, ¿te guío para crearla?"
  Guidance: "Explicar qué se configura allí (Client ID, Redirect URIs, usuarios permitidos). No pedir que pegue secretos en el chat ni en archivos versionados."
  Answer: "App creada; Client ID df3caeb1d0f94b5db0fc0072b248cf53"
  DecidedOn: 2026-09-28

SPOTIFY-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [SPOTIFY-001]
  Question: "¿Puedes proporcionar el Client ID (público) y confirmar que el Client Secret quedará solo en variables de entorno del backend (nunca en el código ni en el frontend)?"
  Guidance: "Indicar exactamente los nombres de variables: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI."
  Answer: "Sí - Client ID en .env; Client Secret jamás en chat ni en código"
  DecidedOn: 2026-09-28

SPOTIFY-003:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [SPOTIFY-001, DEPLOY-001]
  Question: "¿Cuáles serán las Redirect URIs (local y producción)?"
  Guidance: "Verificar en la documentación vigente las reglas de HTTPS/loopback. Deben coincidir exactamente con las registradas."
  Answer: "Dev: http://127.0.0.1:5173/callback · Prod: https://migmusic.vercel.app/api/auth/callback"
  DecidedOn: 2026-09-28

SPOTIFY-004:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [DEPLOY-001]
  Question: "¿En qué entorno se desplegará (dominio/URL final) para configurar OAuth y CORS correctamente?"
  Guidance: "Se conecta con DEPLOY-001 y DEPLOY-002."
  Answer: "https://migmusic.vercel.app (proxy /api/* hacia Render)"
  DecidedOn: 2026-09-28

SPOTIFY-005:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-004]
  Question: "Para usar el Web Playback SDK se requiere una cuenta Spotify Premium: ¿confirmas que tendrás una para desarrollar y demostrar?"
  Guidance: "Si no, proponer alternativa: modo demo sin reproducción Spotify o reproducción vía Spotify Connect; registrar el impacto en el alcance."
  Answer: "Sí - cuenta Premium confirmada (CONS-004)"
  DecidedOn: 2026-09-28

SPOTIFY-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [SPOTIFY-001]
  Question: "¿Qué funciones de Spotify quieres exactamente: buscar canciones, ver tus playlists, agregar canciones de búsqueda a la lista, ver tus canciones guardadas?"
  Guidance: "Determina los scopes. Aplicar mínimo privilegio y verificar disponibilidad vigente de endpoints."
  Answer: "C - buscar, playlists propias, guardadas, seguir artistas/álbumes"
  DecidedOn: 2026-09-28

SPOTIFY-007:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [SPOTIFY-002]
  Question: "¿Cómo quieres manejar la sesión de Spotify (recordar al usuario, cerrar sesión, expiración) y qué debe pasar si el token expira mientras suena algo?"
  Guidance: "Propuesta: cookie HttpOnly + refresh automático en backend."
  Answer: "Cookie HttpOnly segura en backend + refresh automático de access token; si falla refresh, cerrar sesión y avisar al usuario"
  DecidedOn: 2026-09-28

SPOTIFY-008:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001]
  Question: "En móvil, el Web Playback SDK tiene limitaciones de soporte: ¿aceptas que en dispositivos móviles Spotify funcione con una alternativa (por ejemplo controlar el reproductor de Spotify vía Web API) o solo música local?"
  Guidance: "Verificar compatibilidad vigente antes de prometer nada. Registrar en ADR."
  Answer: "A - móvil: música local + Spotify vía Web API (sin SDK en móvil)"
  DecidedOn: 2026-09-28
```

### R8 — Frontend Questions

```yaml
FRONT-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [VIS-006, LOCAL-006, SPOTIFY-008]
  Question: "¿Qué tecnología frontend prefieres (React, Vue, Svelte, otra)?"
  Guidance: "Si no tiene preferencia: comparar brevemente y recomendar una según la complejidad del estado del reproductor, ecosistema de animación y curva de aprendizaje. Debe permitir estructura POO clara."
  Answer: "A - React + Vite"
  DecidedOn: 2026-09-28

FRONT-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [FRONT-001]
  Question: "¿Quieres TypeScript?"
  Guidance: "Recomendar TypeScript: interfaces y clases abstractas hacen más visible la POO y la arquitectura."
  Answer: "Sí - TypeScript"
  DecidedOn: 2026-09-28

FRONT-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [VIS-006]
  Question: "¿Qué nivel de animación técnica quieres implementar (CSS puro, animaciones por librería, canvas/WebGL)?"
  Guidance: "Relacionar con VIS-006 y rendimiento."
  Answer: "A - CSS puro sobre transform/opacity, con prefers-reduced-motion; sin canvas/WebGL"
  DecidedOn: 2026-09-28

FRONT-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-003]
  Question: "¿Prefieres alguna librería de animaciones (Framer Motion, GSAP, Motion One, anime.js u otra)?"
  Guidance: "Si no, recomendar según FRONT-001."
  Answer: "Ninguna libreria; CSS puro (cierra FRONT-003 = A)"
  DecidedOn: 2026-09-28

FRONT-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001]
  Question: "¿Qué estrategia de estado y estilos prefieres (stores, context, CSS Modules, Tailwind, etc.) o delego la recomendación?"
  Guidance: "Debe respetar la separación de UI y lógica."
  Answer: "CSS Modules + Zustand (mantiene tokens.css de F1 y da stores minimos para playlist y reproductor)"
  DecidedOn: 2026-09-28

FRONT-006:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001]
  Question: "¿Qué estrategia responsive quieres (mobile-first, breakpoints específicos, layout distinto por dispositivo)?"
  Guidance: "Proponer mobile-first con 4 rangos: mobile, tablet, laptop, desktop. Confirmar."
  Answer: "Mobile-first con breakpoints sm 640 / md 1024 / lg 1440; reproductor central y lista debajo (VIS-012)"
  DecidedOn: 2026-09-28
```

### R9 — Backend Questions

```yaml
BACK-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [ARCH-002, SPOTIFY-002]
  Question: "¿Qué framework Python quieres usar (FastAPI, Flask, Django)?"
  Guidance: "Si no tiene preferencia: FastAPI (tipado, async, validación con Pydantic, OpenAPI automática, bueno para arquitectura limpia); Flask (minimalista, más manual); Django (completo, más pesado, ORM/admin). Explicar y recomendar."
  Answer: "A - FastAPI"
  DecidedOn: 2026-09-28

BACK-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [BACK-001]
  Question: "¿Qué versión de Python y gestor de dependencias usarás (venv+pip, Poetry, uv)?"
  Guidance: "Alinear con CONS-003."
  Answer: "A - uv (fallback a venv+pip si no está disponible)"
  DecidedOn: 2026-09-28

BACK-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [BACK-001]
  Question: "¿Qué herramientas de calidad de código quieres (ruff, black, mypy, pre-commit)?"
  Guidance: "Recomendar type hints estrictos para reforzar POO."
  Answer: "A - ruff + mypy estricto"
  DecidedOn: 2026-09-28
```

### R10 — Database Questions

```yaml
DB-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [PLAYLIST-001, LOCAL-007, BACK-001]
  Question: "¿Quieres persistencia de playlists en el servidor (que sobrevivan entre dispositivos y sesiones) o basta con memoria/almacenamiento local?"
  Guidance: "Explicar cuándo REALMENTE se necesita base de datos: múltiples dispositivos, cuentas de usuario, compartir playlists. Si solo hay una sesión y datos locales, no es necesaria y añadirla es sobreingeniería."
  Answer: "Sí - persistencia de playlists en servidor"
  DecidedOn: 2026-09-28

DB-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DB-001]
  Question: "Si se necesita base de datos: ¿SQLite, PostgreSQL u otra?"
  Guidance: "SQLite: simple, archivo único, ideal en desarrollo/demo pero cuidado con discos efímeros en cloud. PostgreSQL: robusto, apto para producción. Recomendar según DEPLOY-001."
  Answer: "A - PostgreSQL en Neon (plan gratuito)"
  DecidedOn: 2026-09-28

DB-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DB-002]
  Question: "¿Cómo se guardará el orden de la lista enlazada en la base de datos (columnas prev/next, campo position, u otra estrategia) y aceptas reconstruir la DoublyLinkedList al cargar?"
  Guidance: "Explicar el mapeo objeto-relacional de una estructura enlazada y sus trade-offs. Mantener el dominio libre de ORM (Repository)."
  Answer: "B - columnas prev_id/next_id reflejando el enlace; DLL se reconstruye al cargar"
  DecidedOn: 2026-09-28

DB-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DB-001]
  Question: "Con playlists guardadas en el servidor, ¿quién puede leerlas y editarlas? No hay cuentas de MigMusic."
  Guidance: "Opciones: (a) sin cuentas, UUID opaco de acceso por enlace; (b) dueño = sesión de Spotify; (c) cuentas propias con registro/login."
  Answer: "A - sin cuentas; UUID opaco. Añadir dueño después es una columna extra"
  DecidedOn: 2026-09-28
```

### R11 — Additional Features Questions

> El agente **debe proponer como mínimo 2** funcionalidades adicionales y **no agregarlas automáticamente**. Para cada propuesta: qué hace, por qué es útil, complejidad aproximada e impacto en la arquitectura. Candidatas: Shuffle, Repeat, Favorites, History, Queue, Search, Filters, Audio visualizer, Equalizer, Keyboard shortcuts, Multiple playlists, Sleep timer, Playback speed. (Excluir las que el usuario ya haya aceptado/rechazado antes.)

```yaml
FEAT-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [R4, R5, R6, R7]
  Question: "Te propongo estas funcionalidades adicionales (con explicación de cada una). ¿Cuáles quieres incluir? (mínimo 2 para cumplir el taller)"
  Guidance: "Presentar tabla: funcionalidad | qué hace | utilidad | complejidad | impacto arquitectónico. Registrar cada una como sub-entrada FEAT-001-<nombre> con CONFIRMED o REJECTED."
  Answer: "Elegidas b, c, d, e (4 funcionalidades; mínimo 2 requerido)"
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
  Question: "Favoritos: marcar canción con corazón (flag en Song + vista)"
  Guidance: "Bajo coste, impacto en Song + UI."
  Answer: "CONFIRMED"
  DecidedOn: 2026-09-28

FEAT-001-c:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Búsqueda dentro de la playlist usando find()"
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
  Question: "¿Alguna funcionalidad propia que quieras agregar y que no esté en la lista?"
  Guidance: "Evaluar impacto y clasificarla."
  Answer: null
  DecidedOn: null

FEAT-003:
  Status: PENDING
  Priority: NORMAL
  DependsOn: [FEAT-001]
  Question: "Para las funcionalidades aceptadas, ¿en qué orden de prioridad las implementamos?"
  Guidance: "Reflejar en el Roadmap."
  Answer: null
  DecidedOn: null
```

### R12 — Deployment Questions

```yaml
DEPLOY-001:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [CONS-005, FRONT-001, BACK-001, DB-001]
  Question: "¿Dónde quieres desplegar MigMusic (Vercel, Render, Railway, Fly.io, AWS, Azure, Google Cloud, otro)?"
  Guidance: "Si no tiene preferencia: recomendar una arquitectura (ej. frontend estático en Vercel/Netlify + backend Python en Render/Railway/Fly.io + PostgreSQL gestionado si aplica), explicando por qué, costos y limitaciones (arranque en frío, disco efímero)."
  Answer: "A - Vercel (frontend) + Render (backend)"
  DecidedOn: 2026-09-28

DEPLOY-002:
  Status: CONFIRMED
  Priority: CRITICAL
  DependsOn: [DEPLOY-001]
  Question: "¿Frontend y backend estarán en el mismo dominio (o subdominios) o en dominios distintos?"
  Guidance: "Determina CORS, cookies SameSite y la Redirect URI de Spotify."
  Answer: "X - proxy /api/* en Vercel: un solo origen (migmusic.vercel.app)"
  DecidedOn: 2026-09-28

DEPLOY-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DEPLOY-001]
  Question: "¿Quieres CI/CD (GitHub Actions) con despliegue automático al hacer push?"
  Guidance: "Recomendar como mínimo: lint + tests en cada PR."
  Answer: "Sí - GitHub Actions con lint y tests que bloquean"
  DecidedOn: 2026-09-28

DEPLOY-004:
  Status: REJECTED
  Priority: NORMAL
  DependsOn: [DEPLOY-001]
  Question: "¿Quieres contenedores Docker para desarrollo y producción?"
  Guidance: "Ayuda a reproducibilidad; puede ser obligatorio según la plataforma."
  Answer: "No aplica por CONS-003 (entorno sin Docker)"
  DecidedOn: 2026-09-28

DEPLOY-005:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DEPLOY-001]
  Question: "¿Qué nivel de logs y monitoreo quieres (logs estructurados, healthcheck, alertas)?"
  Guidance: "Nunca registrar tokens ni datos sensibles."
  Answer: "Vercel: miguelcebing; Render y Neon conectadas vía GitHub. Logs estructurados básicos + healthcheck (recomendado, 0 $)"
  DecidedOn: 2026-09-28
```

### R13 — Testing Questions

```yaml
TEST-001:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [FRONT-001, BACK-001]
  Question: "¿Qué herramientas de prueba prefieres (pytest en backend; Vitest/Jest y Playwright/Cypress en frontend) o delego la recomendación?"
  Guidance: "Recomendar pytest + herramienta nativa del bundler + Playwright."
  Answer: "A - pytest + Vitest + Playwright"
  DecidedOn: 2026-09-28

TEST-002:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [TEST-001]
  Question: "¿Qué cobertura mínima esperas (por ejemplo ≥ 90 % en el dominio y la lista doblemente enlazada)?"
  Guidance: "Proponer umbrales por capa."
  Answer: "≥95% en domain/ (núcleo académico) y ≥80% global; el CI lo bloquea"
  DecidedOn: 2026-09-28

TEST-003:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [DEPLOY-003]
  Question: "¿Quieres que las pruebas se ejecuten automáticamente en CI y bloqueen el despliegue si fallan?"
  Guidance: "Recomendado."
  Answer: "Sí - los tests corren en CI y bloquean (implícito en DEPLOY-003)"
  DecidedOn: 2026-09-28

TEST-004:
  Status: CONFIRMED
  Priority: NORMAL
  DependsOn: [TEST-001]
  Question: "¿Quieres tests property-based con hypothesis para los invariantes de la lista?"
  Guidance: "SKILL2 lo propone como opcional; añade una dependencia de desarrollo."
  Answer: "Sí - hypothesis para invariantes y secuencias aleatorias"
  DecidedOn: 2026-09-28
```

---

## Implementation Gate

El agente **NO** escribe código de aplicación (más allá de exploración o prototipos descartables explícitamente anunciados) hasta que se cumplan **todas** estas condiciones:

- [x] Todas las preguntas con `Priority: CRITICAL` están en `CONFIRMED` o `REJECTED`.
- [x] **Arquitectura:** `ARCH-001`, `ARCH-002` confirmadas.
- [x] **Frontend:** `FRONT-001`, `FRONT-002` confirmadas.
- [x] **Backend:** `BACK-001` confirmada (Python).
- [x] **Spotify:** `SPOTIFY-001`…`SPOTIFY-005` confirmadas.
- [x] **Reproducción local:** `LOCAL-001`, `LOCAL-006` confirmadas.
- [x] **Diseño principal:** `VIS-001`, `VIS-006`, `VIS-012` confirmadas.
- [x] **Estrategia de playlist:** `PLAYLIST-001`, `PLAYLIST-009` confirmadas.
- [x] **Lista doblemente enlazada:** ubicación (`ARCH-001`) y comportamiento en extremos (`PLAYLIST-009`) confirmados.
- [x] **Deployment:** `DEPLOY-001`, `DEPLOY-002` confirmadas.
- [x] Ninguna pregunta adicional creada por el agente con prioridad `CRITICAL` sigue `PENDING`.
- [x] El agente ha presentado un **resumen de decisiones** y el usuario ha dicho explícitamente que puede empezar.

**Excepciones:** las preguntas `NORMAL` pendientes **no bloquean** el gate; se preguntan en la fase del roadmap donde se necesiten (registrando el momento en el Decision Log).

---

## Reglas para decisiones técnicas

Cuando surja una decisión técnica no definida, el agente:

1. Explica **brevemente** las opciones.
2. Expone **ventajas y desventajas** de cada una.
3. **Recomienda** una opción técnicamente razonable y dice por qué.
4. **Pregunta** cuál prefiere el usuario.
5. **Registra** la decisión (Answer + Decision Log + ADR si es arquitectónica).

Nunca asume la elección del usuario. Si el usuario delega ("lo que recomiendes"), la recomendación pasa a `PROPOSED` y se pide un "sí" explícito.

## Interpretación de respuestas

- **Respuesta clara:** registrar literal + resumen, `CONFIRMED`.
- **Respuesta ambigua:** reformular con una pregunta de confirmación; mantener `PROPOSED`.
- **Respuesta parcial:** confirmar la parte resuelta; crear sub-pregunta `-a` para la pendiente.
- **Respuesta contradictoria con otra decisión:** señalar el conflicto, explicar consecuencias y pedir que elija; actualizar ambas.
- **"No quiero X":** `REJECTED`; no volver a proponer.
- **Cambio de opinión posterior:** reabrir (`CONFIRMED → PENDING`), evaluar impacto en código ya escrito y en el gate, registrar en Decision Log.

## Preguntas adicionales (cuándo crearlas)

El agente crea nuevas preguntas cuando:

- Una respuesta introduce una tecnología o funcionalidad nueva sin decisiones asociadas.
- Hay una incompatibilidad técnica descubierta (ej. visualizador de audio con Spotify SDK).
- Aparece una limitación de las plataformas (Spotify, navegadores, cloud) que cambia el alcance.
- La respuesta del usuario es demasiado vaga para implementar.
- Se descubre una dependencia entre decisiones no prevista.

Convención de IDs nuevos: `<PREFIJO>-<número>` siguiente disponible, o sufijo de letra (`LOCAL-006a`) cuando derive de otra.

---

## Roadmap

> Las fases se ajustan tras la entrevista. Cada fase termina con pruebas verdes y actualización de este archivo.

| Fase | Contenido | Skills |
|---|---|---|
| **F0 — Entrevista y gate** | Rondas R1–R13, resumen de decisiones, aprobación para empezar. | `requirements-interview` |
| **F1 — Fundaciones** | Repositorio, estructura de carpetas (8.2), tooling, config por entorno, logging, CI base. | `backend-architecture-python`, `testing-quality` |
| **F2 — Núcleo de dominio** | `Node`, `DoublyLinkedList`, `Song`, `Playlist` + suite de pruebas completa. | `doubly-linked-list`, `testing-quality` |
| **F3 — Servicios y API** | `PlaylistService`, `PlaybackService`, rutas, schemas, manejo de errores. | `backend-architecture-python` |
| **F4 — Frontend base** | Layout, design tokens, componentes, cliente API, controladores. | `ui-ux-design` |
| **F5 — Audio local** | `LocalAudioPlayer`, File Picker, seek, skip N seg, volumen, persistencia si se aprobó. | `local-audio` |
| **F6 — Spotify** | OAuth, sesión, búsqueda, `SpotifyPlayer` con Web Playback SDK, manejo de errores. | `spotify-integration` |
| **F7 — Integración** | Playlist unificada, cambio entre players, vista didáctica de la lista. | todas |
| **F8 — Funcionalidades adicionales** | Las aprobadas en `FEAT-*`. | según cada una |
| **F9 — Pulido** | Animaciones, responsive, accesibilidad, rendimiento. | `ui-ux-design` |
| **F10 — Despliegue** | Cloud, HTTPS, CORS, Redirect URI de producción, logs. | `deployment-cloud` |
| **F11 — Cierre** | E2E, documentación final, checklist de aceptación, demo. | `testing-quality` |

---

## Criterios de aceptación

**Lista doblemente enlazada**
- [x] `Node`/`DoublyLinkedList` implementados con enlaces reales `previous`/`next`, `head`, `tail`, `current`, `size`.
- [x] Todas las operaciones mínimas de la sección 9 implementadas y probadas, incluidos casos borde.
- [x] La playlist activa usa la lista (no un array) y el agente puede explicar cómo.

**Reproductor**
- [x] Play, Pause, Next, Previous, Seek, Volume, Mute funcionan con audio real. (E2E `master-flow`, desktop + móvil, con WAV real)
- [x] Skip forward y skip backward mueven exactamente N segundos configurados (`PLAYER-001/002`) sin salirse de los límites de la pista. (E2E + unit tests de `PlaybackService`/clamp)
- [x] Agregar (inicio/final/posición), eliminar y seleccionar canción funcionan desde la UI. (E2E: 3 pistas, insert en índice 1, quitar la activa)

**Fuentes**
- [x] Música local: File Picker, reproducir/pausar/seek/cambiar/eliminar. (E2E con `setInputFiles`)
- [ ] Spotify: login OAuth completo, refresh de token, reproducción con Web Playback SDK (con cuenta Premium), errores manejados. *(2026-10-01: callback verificado en producción — `state` firmado sin cookie llega hasta Spotify (antes: 401), cookie + `state` falsificado → 422, sin nada → 401; la respuesta `invalid_grant` y no `invalid_client` confirma credenciales reales de la app. Queda la demo manual con cuenta Premium: autorizar, buscar y reproducir con el Web Playback SDK)*
- [x] Spotify y local se tratan como fuentes separadas y polimórficas. (`AudioSource` en F5, unit tests de `SpotifyPlayer`/`LocalAudioPlayer`)

**Arquitectura y código**
- [x] Estructura por capas visible y respetada (sin lógica en rutas/componentes).
- [x] POO: abstracciones (ABC/interfaces), polimorfismo, inyección de dependencias, SOLID justificable. (`create_app` + repositorios/polimorfismo de reproducción, ADR-001/005)
- [x] Backend 100 % Python. Código en inglés.
- [x] Sin secretos en repositorio ni en frontend; `.env.example` presente.

**Interfaz**
- [x] Refleja las decisiones `VIS-*`/`UX-*` confirmadas; animaciones acordes; `prefers-reduced-motion` respetado. (`tokens.css` + Framer Motion con `MotionConfig reducedMotion="user"`, F9-GATE/F4-ANIM)
- [x] Responsive verificado en mobile, tablet, laptop y desktop. (breakpoints 640/1024/1440 + E2E en Pixel 7)
- [x] Accesibilidad básica cumplida (teclado, foco, ARIA, contraste). (axe WCAG 2.1 A/AA sin violaciones + focus-trap en E2E)

**Calidad y despliegue**
- [x] Pruebas unitarias/integración/e2e pasando; cobertura acorde a `TEST-002`. (317 pytest/97.06 %/dominio 100 %, 80 Vitest, 9 E2E; ver `docs/testing.md`)
- [x] Desplegado en la nube con HTTPS, CORS correcto, Redirect URI de producción, logs y configuración de producción. *(verificado 2026-10-01 sobre `19e9408`: `https://migmusic.vercel.app` → proxy `/api/*` → `https://migmusic-api.onrender.com`; health 200 directo y por proxy, preflight 200 con ACAO `https://migmusic.vercel.app` + `credentials: true`, Spotify acepta la Redirect URI registrada, Render y Vercel auto-desplegaron el push y el workflow `keep-alive` vigila `/api/health` cada 10 min)*
- [x] Al menos 2 funcionalidades adicionales aprobadas por el usuario e implementadas. (`FEAT-001-b/c/d/e`: favoritos, búsqueda, repeat, drag & drop)
- [x] Documentación (README, docs/architecture, ADRs) actualizada.

---

## Decision Log

> El agente añade una línea por cada decisión o cambio. Formato: `AAAA-MM-DD | ID | Decisión | Motivo/Impacto`.

| Fecha | ID | Decisión | Motivo / Impacto |
|---|---|---|---|
| 2026-09-28 | CONS-001 | Académico + producto; límite 2026-10-02 | Fija plazo: 4 días, recorte de alcance negociado |
| 2026-09-28 | CONS-002 | Trabajo solo | Sin revisión por pares; nivel en CONS-002a |
| 2026-09-28 | CONS-003 | Windows/VS Code/Python 3.11-3.13/Node 26; sin Docker | DEPLOY-004 pasa a REJECTED; scripts .ps1 |
| 2026-09-28 | CONS-004 | Cuenta Spotify Premium disponible | Web Playback SDK viable en desktop |
| 2026-09-28 | CONS-005 | Solo planes gratuitos | Vercel + Render + Neon free; UptimeRobot |
| 2026-09-28 | CONS-006 | Interfaz en español e inglés | Añade capa i18n en F4 |
| 2026-09-28 | CONS-001a | Alcance A (recomendado) | RNF/FEAT recortadas; 4 FEAT en F8 |
| 2026-09-28 | VIS-001 | Estilo retro/vinilo | Define tokens y microinteracciones |
| 2026-09-28 | VIS-002 | Tema dual con selector | Dos paletas de design tokens |
| 2026-09-28 | VIS-003 | Azul marino/eléctrico + negro | Base de la paleta |
| 2026-09-28 | VIS-004 | #1E6BFF + #4338CA sobre #0A0D14 | Design tokens F4 |
| 2026-09-28 | VIS-005 | Sin gradientes | Ahorro de implementación |
| 2026-09-28 | VIS-006 | Animaciones sutiles | CSS/WAAPI + prefers-reduced-motion |
| 2026-09-28 | VIS-007 | Sin visualizador | Excluido por CONS-001a |
| 2026-09-28 | VIS-008 | Sin waveform | Excluido por CONS-001a |
| 2026-09-28 | VIS-012 | Layout B: reproductor central + lista | Estructura de layouts F4 |
| 2026-09-28 | UX-001 | Filas con portada | Componente SongRow |
| 2026-09-28 | UX-002 | Vista de nodos alternable | Panel didáctico para sustentación |
| 2026-09-28 | UX-003 | Modal con pestañas Local/Spotify + posición | Cubre RF-07 íntegro |
| 2026-09-28 | UX-004 | Toasts + estado vacío | Manejo de errores global |
| 2026-09-28 | PLAYER-001 | Avanzar 5 s | Constante SKIP_FORWARD_SECONDS |
| 2026-09-28 | PLAYER-002 | Retroceder 5 s | Constante SKIP_BACKWARD_SECONDS |
| 2026-09-28 | PLAYER-002a | Si posicion <= 5 s -> pista anterior | Regla de borde en PlaybackService |
| 2026-09-28 | PLAYER-003 | Autoplay con moveNext | evento ended + moveNext |
| 2026-09-28 | PLAYER-004 | Shuffle por índice (estrategia b) | Lista intacta; historial separado |
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
| 2026-09-28 | PLAYLIST-008 | Búsqueda con find | FEAT-001-c |
| 2026-09-28 | PLAYLIST-009 | Parada en extremos | DLL no circular; repeat como modo |
| 2026-09-28 | ARCH-001 | DLL solo en backend Python | Decisiones de red en Next/Previous; tramo inicial de C |
| 2026-09-28 | ARCH-002 | Hexagonal por capas + DI | Estructura §8.2 fijada |
| 2026-09-28 | ARCH-003 | ADRs + Mermaid | Evidencia para sustentación |
| 2026-09-28 | LOCAL-001 | MP3 + WAV | Validación MIME/extensión |
| 2026-09-28 | LOCAL-002 | Selección múltiple | Orden: al final |
| 2026-09-28 | LOCAL-003 | Drag and drop de archivos | Complementa File Picker |
| 2026-09-28 | LOCAL-004 | ID3 en navegador | Privacidad: no se suben archivos |
| 2026-09-28 | LOCAL-006 | Solo metadatos + re-selección | Sin blobs; LOCAL-006a pendiente |
| 2026-09-28 | LOCAL-007 | Playlists también en navegador | IndexedDB como respaldo |
| 2026-09-28 | LOCAL-008 | IndexedDB | Almacenamiento local gratuito |
| 2026-09-28 | SPOTIFY-001 | App creada; Client ID df3caeb... | Base de OAuth |
| 2026-09-28 | SPOTIFY-002 | Secretos solo en variables de entorno | RNF-07 |
| 2026-09-28 | SPOTIFY-003 | 127.0.0.1:5173 y vercel.app/api/auth/callback | localhost prohibido desde 27/11/2025 |
| 2026-09-28 | SPOTIFY-004 | Producción en migmusic.vercel.app | CORS y OAuth sobre un origen |
| 2026-09-28 | SPOTIFY-005 | Premium confirmada | SDK habilitado en desktop |
| 2026-09-28 | SPOTIFY-006 | Alcance C (buscar, playlists, guardadas, seguir) | Scopes a verificar en F6 |
| 2026-09-28 | SPOTIFY-008 | Móvil sin SDK, vía Web API | Polimorfismo de players |
| 2026-09-28 | FRONT-001 | React + Vite | Base del frontend |
| 2026-09-28 | FRONT-002 | TypeScript | POO visible y verificable |
| 2026-09-28 | BACK-001 | FastAPI | Validación Pydantic + OpenAPI |
| 2026-09-28 | BACK-002 | uv | pyproject.toml único |
| 2026-09-28 | BACK-003 | ruff + mypy estricto | RNF-04/08 |
| 2026-09-28 | DB-001 | Persistencia en servidor | Postgres obligatorio por PLAYLIST-001 |
| 2026-09-28 | DB-002 | Neon (gratuito) | Sobrevive a discos efímeros de Render |
| 2026-09-28 | DB-003 | prev_id/next_id + reconstrucción | Mantiene el dominio libre de ORM |
| 2026-09-28 | FEAT-001 | Elegidas b, c, d, e | Cumple mínimo de 2 del taller |
| 2026-09-28 | FEAT-001-a | Atajos: REJECTED | Fuera de alcance |
| 2026-09-28 | FEAT-001-b | Favoritos: CONFIRMED | F8 |
| 2026-09-28 | FEAT-001-c | Búsqueda: CONFIRMED | F8 |
| 2026-09-28 | FEAT-001-d | Repeat: CONFIRMED | F8 |
| 2026-09-28 | FEAT-001-e | Drag and drop: CONFIRMED | F8 |
| 2026-09-28 | DEPLOY-001 | Vercel + Render | Arquitectura de despliegue |
| 2026-09-28 | DEPLOY-002 | Proxy /api/* en Vercel | Un origen: sin CORS ni SameSite=None |
| 2026-09-28 | DEPLOY-003 | CI con GitHub Actions | Lint + tests bloquean |
| 2026-09-28 | DEPLOY-004 | Sin Docker | No aplica por CONS-003 |
| 2026-09-28 | DEPLOY-005 | Cuentas Vercel(miguelcebing)/Render/Neon vía GitHub | Listo para F10 |
| 2026-09-28 | TEST-001 | pytest + Vitest + Playwright | F11 |
| 2026-09-28 | TEST-003 | CI bloquea el despliegue | Calidad por fase |
| 2026-09-28 | GATE | Implementation Gate aprobado por el usuario (sí empieza) | Autoriza F1+; entrevista F0 completada |
| 2026-09-28 | D0-INIT | Repo inicial: .gitignore / .env.example / README / .gitattributes | Secretos fuera de git; primer push a GitHub |
| 2026-09-28 | D0-TREE | AGEND.md a la raíz y .agents/ -> skills/ | ARCH-002: coincide con el árbol 8.2 aprobado |
| 2026-09-28 | F1-TOOL | uv + ruff + mypy estricto + pytest; eslint/tsc/vitest en frontend | BACK-002/003 y TEST-001; el CI bloquea en cada push |
| 2026-09-28 | F1-CORE | Settings falla al arrancar si falta una variable obligatoria | SKILL1 §4; el Client Secret jamás llega al frontend |
| 2026-09-28 | F1-LOG | Logging JSON por línea con redacción de claves sensibles | DEPLOY-005; nunca se registran tokens |
| 2026-09-28 | F1-HTTP | error_handlers.py único: excepciones de dominio -> HTTP | SOLID; los routers no capturan excepciones |
| 2026-09-28 | F1-PROXY | Vite proxy /api -> 127.0.0.1:8000 en desarrollo | Un solo origen también en local, como en producción |
| 2026-09-28 | F1-CI | GitHub Actions: backend + frontend + chequeo de secretos | DEPLOY-003 y TEST-003: bloquean el despliegue |
| 2026-09-28 | F1-DOCS | ADR-001..004 + architecture.md con diagramas Mermaid | ARCH-003; evidencia para la sustentación |
| 2026-09-28 | TEST-002 | Cobertura ≥95% dominio y ≥80% global | Umbrales en pyproject + CI |
| 2026-09-28 | PLAYLIST-009a | Extremos retornan bool, sin excepción | Flujo normal sin try/except |
| 2026-09-28 | PLAYLIST-009b | Al borrar current, pasa a next (o prev si era tail) | No se pierde la posición en la UI |
| 2026-09-28 | PLAYLIST-002 | Crear playlists habilitado | Requerido por PLAYLIST-001=B |
| 2026-09-28 | PLAYLIST-003 | Renombrar playlists habilitado | Requerido por PLAYLIST-001=B |
| 2026-09-28 | TEST-004 | Tests property-based con hypothesis | Invariantes de la lista verificables |
| 2026-09-28 | F2-DLL | Node + DoublyLinkedList con nodos reales (prohibido array) | ARCH-001=A y sección 9; invariantes verificables en cada operación |
| 2026-09-28 | F2-EDGE | move_next/move_previous retornan bool y paran en los extremos | PLAYLIST-009=A + 009a; sin excepciones en el flujo normal |
| 2026-09-28 | F2-CURSOR | Al borrar current pasa al siguiente (al anterior si era tail) | PLAYLIST-009b; no se pierde la posición al eliminar desde la UI |
| 2026-09-28 | F2-PLAYLIST | Playlist compone la lista; crear y renombrar habilitados | PLAYLIST-001=B, 002 y 003; duplicados permitidos (sin decisión en contra) |
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
| 2026-09-28 | F6-GATE | OAuth PKCE + sesión HttpOnly + proxy Web API + SpotifyPlayer (Web Playback SDK) | SPOTIFY-001/002/003/005/006/007/008, F6-STATE, F6-SCOPES, ADR-005; backend: ruff/mypy/262 tests; frontend: typecheck/lint/40 tests/build OK |
| 2026-09-28 | F6-STATE | Sesión Spotify con cookie HttpOnly + refresh automático en backend | SPOTIFY-007; token en backend, nunca en frontend |
| 2026-09-28 | F6-SCOPES | Scopes: streaming, user-read-*, user-modify-playback-state, playlist-read-private, user-library-read | SPOTIFY-006 opción C; mínima privilegio |
| 2026-09-28 | F7-GATE | PlaybackController reescrito: seek/skip audibles, fin de pista con repeat, cambio local<->Spotify sin doble audio, volumen en vivo y vista didáctica animada | RF-12, PLAYER-001..004/007/011, UX-002; backend: ruff/mypy/262 tests/97%; frontend: lint/typecheck/58 tests/build OK |
| 2026-09-29 | F8-GATE | Favoritos (flag en Song + endpoint idempotente), búsqueda con find en la lista (Enter resalta el primer match), repeat verificado y reordenar con drag & drop | FEAT-001-b/c/d/e, PLAYLIST-005/008; backend: ruff/mypy/284 tests/97%; frontend: lint/typecheck/69 tests/build OK |
| 2026-09-29 | F9-GATE | Pulido: contraste AA con tokens *-text por tema, focus trap + aria-current + group label, tema inicial prefers-color-scheme, code-splitting de music-metadata (main 406→288 kB), cursor grab, touch targets 44px | RNF-06, RNF-10, VIS-006/012, F4-RESPONSIVE, SKILL5; frontend: lint/typecheck/69 tests/build OK |
| 2026-09-29 | F10-GATE | Despliegue: SqlPlaylistRepository (psycopg, upsert+rewrite en transacción, prev_id/next_id + position), render.yaml (blueprint), vercel.json (rewrite /api/* + x-vercel-enable-rewrite-caching: 0), ADR-006 verificación de plataforma | DB-001/002/003/004, DEPLOY-001..005, ADR-003/004/006; backend: ruff/mypy/292 tests/96.96%/dominio 100% |
| 2026-09-29 | F11-GATE | Cierre: suite E2E Playwright (smoke, flujo maestro en desktop + móvil, accesibilidad axe WCAG 2.1 A/AA), fix del crash de arranque detectado por E2E (`hasTrack` con `playback: null`), job `e2e` en CI, `docs/testing.md` (reporte criterio → evidencia → estado) | TEST-001/002/003/004 y SKILL6; backend: 292 tests/96.96%/dominio 100%; frontend: lint/tsc/69 tests/7 E2E/build; axe: 0 violaciones |
| 2026-09-30 | DEPLOY-GATE | Despliegue real ejecutado: Vercel proyecto `migmusic` (`https://migmusic.vercel.app`, rewrite `/api/*`), Render `migmusic-api` (`srv-dau8psugekts73del56g`, rootDir `backend`, auto-deploy por commit), Neon `MigMusic` (`DATABASE_URL` fuera del repo en `deploy/credentials.env`) | DEPLOY-001..005, ADR-006; health 200 directo y por proxy, CORS preflight 200 con ACAO correcto, deploy `7f256c6` live |
| 2026-09-30 | DEPLOY-FIX | Root Directory `frontend` en el proyecto Vercel (el build de Git ejecutaba `vite build` en la raíz del repo) e integración Git conectada | Auto-deploy de Vercel operativo (commit → Ready en ~13 s y alias `migmusic.vercel.app`); verificado con `60ab478` |
| 2026-10-01 | F4-ANIM | Se revoca la decisión de "CSS puro": se instala Framer Motion para las microinteracciones de PlayerControls, TrackList, AddTrackDialog y ProgressBar | Anula la línea F4-ANIM del 2026-09-28; MotionConfig `reducedMotion="user"` y los tokens CSS siguen garantizando VIS-006/FRONT-003/004; gates: tsc, eslint, 77 Vitest, build y 8 E2E OK |
| 2026-10-01 | UX-FIX | Tres correcciones: (1) `AddTrackDialog` con `max-height` + cuerpo con scroll, acciones fijas y contador `Agregar (n)`, (2) siguiente/anterior siempre activos —clic en el borde = toast informativo y la música sigue— y seek ±5 s en lugar de 10 s, (3) aislamiento de playlists locales por cabecera `X-Device-Id` (`UX-010`: solo playlists, reproductor global, sin cabecera ⇒ vista completa para E2E/smoke, wipe de Neon al cierre) | Plan de 3 fases aprobado; backend: ruff/mypy/327 tests/97.08%/dominio 100%, frontend: lint/tsc/88 tests/build, E2E: 12 (`spotify-dialog`, `transport-edges`, `device-isolation`); auto-deploy Vercel/Render tras el push y smoke en vivo en esta misma entrega |
| 2026-10-01 | PLAYER-GATE | Reproductor en 7 fases: (1) resiliencia ante reinicio del backend — `next_index`/`previous_index` en `PlaybackOut`, `404 no_active_playback` con reconstrucción de contexto (open + select) y reintento, sync de `activeId` con la playlist que suena al cargar, (2) guarda de secuencia en los reportes de posición (respuestas stale descartadas), (3) UI optimista con rollback en play/pause, seek, ±5 s, siguiente/anterior (la pista destino se precarga en el reproductor), (4) hílo principal: selectors por campo en zustand, `position` aislado a 1 Hz, `ProgressBar` auto-suscrito, `memo` en componentes y drag estable por índice, (5) limpieza de código muerto (`getPlayback`, `hasUserGesture`, `errorKey`, `addSong`, loaders privados), (6) E2E `playback-reload` y `auto-advance` (WAV de 1 s: la pista 2 arranca sola y la cola se detiene con `repeat=off`), (7) gates y docs | Plan `.opencode/plans/reproductor-perf-fix.md` (aprobado); backend: ruff/mypy/334 tests/97.13%/dominio 100%, frontend: lint/tsc/96 tests/build, E2E: 14 (10 specs); CI + auto-deploy Vercel/Render tras el push |
| 2026-10-01 | PLAYER-FIX | Feedback del usuario tras el PLAYER-GATE: (1) error puntual `Spotify player did not report a device id` — `connect()` del SDK pasaba de largo el `ready` con un sondeo de 2 s, dejando un player sin `_deviceId` y creando una segunda instancia (fuga) en el siguiente intento ⇒ `ready` event-driven con tope de 10 s, desconexión en fallo, guarda de `generation` y rechazo inmediato de `initialization_error`/`authentication_error`/`account_error`, (2) transporte percibido como "sin vida"/lento — `load()` sin `pause()` final, `play()` corto si ya suena y `togglePlaying()` gira el botón **antes** de `await player.play()` con `rollbackTo` en `send()` | Backend sin cambios; frontend: lint/tsc/103 tests/build, E2E: 14/14; unit nuevos `spotifySdk.test.ts` (6) + "answers the play click before the player has started the audio"; docs `testing.md` §3/§5 |
| 2026-10-01 | NET-TIMEOUT | Todo request del `apiClient` aborta a los 10 s (`REQUEST_TIMEOUT_MS` con `AbortController`) y el fallo se presenta como `ApiError code="timeout"` → toast localizado `toast.timeout` ("El servidor tardó demasiado en responder") con rollback del parche optimista; `failureMessage(cause, language)` compartido por los cuatro controllers para que ningún timeout llegue en crudo | Evita botones mudos cuando Render free se duerme; frontend: lint/tsc/108 tests/build, E2E: 14/14; unit `apiClient.test.ts` +4 y resilience +1; docs `testing.md` §3/§5 |
| 2026-10-02 | SPEED-FIX | Velocidad de respuesta a los botones (feedback tras NET-TIMEOUT): (1) Render free dormido en cada interacción — el cron `*/10` de `keep-alive.yml` solo disparó 2 de ~50 runs esperados en 8 h (GitHub descarta jobs programados bajo carga, peor en la hora en punto; medido en frío: health 8,6 s directo / 25 s por proxy) ⇒ cron `2-59/5 * * * *` (cada 5 min, nunca en :00, editar el archivo re-registra el schedule) + ping de `/api/health` cada 10 min desde `App.tsx` con la pestaña abierta, (2) un `report` en vuelo anterior al clic pisaba el parche optimista y la UI volvía a la canción vieja mientras la nueva sonaba ⇒ `send()` reserva `lastAppliedSeq = seq` al parchear y `togglePlaying()` reserva antes de `await player.play()`; observación: tras re-registrar el cron en `f51cb79` los 6 slots siguientes no dispararon (0/6) ⇒ el schedule de GitHub no es fiable para este repo, defensa principal = ping del cliente con la pestaña abierta, UptimeRobot pendiente como capa externa | Backend sin cambios; frontend: lint/tsc/110 tests/build, E2E: 14/14; unit optimistic UI +2; docs `testing.md` §3/§5 |
| 2026-10-02 | FLAP-FIX | Siguiente/anterior sonaba la canción nueva ~2 s y volvía a la vieja (feedback tras SPEED-FIX, junto al toast de timeout): (1) el `report` de 1 s disparado después del clic llevaba secuencia mayor y, si el `next` seguía colgado, el backend respondía con la canción anterior y la aplicación íntegra revertía store + audio, (2) en timeout el `rollback(snapshot)` restauraba la vieja a ciegas aunque el comando hubiera aterrizado tarde ⇒ `commit()` abre una ventana de identidad (`intentSeq`) que descarta toda respuesta que cambie de canción hasta que el transporte asiente (con `guardBelow` para las respuestas que corrían dentro de la ventana) y los fallos de desenlace desconocido (`timeout`/`network_error`) conservan el estado optimista —el siguiente `report` reconcilia con la verdad del backend— en lugar de hacer rollback | Backend sin cambios; frontend: lint/tsc/114 tests/build, E2E: 14/14; unit optimistic UI +4; docs `testing.md` §3/§5 |

## Validación de entrega de este AGEND.md

- [x] Contexto del proyecto
- [x] Nombre MigMusic
- [x] Requisitos originales del taller
- [x] Lista doblemente enlazada
- [x] Spotify Web API
- [x] Spotify Web Playback SDK
- [x] Música local
- [x] Backend Python
- [x] Frontend
- [x] Reproductor funcional
- [x] Adelantar segundos
- [x] F4: Layout, design tokens, componentes, API client, controladores
- [x] F5: AudioPlayer, LocalAudioPlayer, metadata ID3, IndexedDB, persistencia local
- [x] F6: OAuth PKCE + sesión, catálogo Spotify (búsqueda/playlists/guardadas), SpotifyPlayer con Web Playback SDK, errores manejados
- [x] F7: Integración - seek/skip/cambio de fuente/fin de pista sincronizados entre backend, players y UI; lista didáctica animada
- [x] F8: Favoritos con corazón, búsqueda en la lista con find (Enter resalta el primer match), filtro de solo favoritas, repeat verificado y reordenar con drag & drop
- [x] F9: Pulido - contraste AA (tokens de texto por tema), accesibilidad (focus trap en diálogo, aria-current, group label, 44px), prefers-color-scheme, reduced-motion, responsive 4 breakpoints y code-splitting de metadata
- [x] F10: Adaptador SQL (Neon) + tests de contrato, render.yaml (blueprint), vercel.json (proxy de un solo origen), ADR-006 (plataformas verificadas) y docs de despliegue actualizadas — el despliegue real en las cuentas (Vercel/Render/Neon/Spotify) lo ejecuta el usuario con la checklist entregada
- [x] F11: Suite E2E Playwright (flujo maestro desktop + móvil, smoke y accesibilidad axe A/AA), fix del bug de arranque que encontró el E2E, job `e2e` en CI, criterios de aceptación actualizados con evidencia y reporte final en `docs/testing.md` — quedan como acción manual del usuario el despliegue en la nube y la demo con cuenta Spotify Premium
- [x] Retroceder segundos
- [x] Diseño animado
- [x] Responsive
- [x] Cloud deployment
- [x] Seguridad
- [x] Testing
- [x] Roadmap
- [x] Criterios de aceptación
- [x] Preguntas para el agente de desarrollo
- [x] IDs únicos para las preguntas
- [x] Estados de las preguntas
- [x] Orden de entrevista
- [x] Dependencias entre preguntas
- [x] Reglas para decisiones técnicas
- [x] POO obligatoria y estructura por capas (requisito adicional)
- [x] Backend completamente en Python (requisito adicional)
