---
name: requirements-interview
description: Conduce la entrevista progresiva de requisitos de MigMusic leyendo AGEND.md, preguntando solo lo PENDING, registrando respuestas, detectando dependencias y controlando el Implementation Gate. Úsala SIEMPRE al iniciar el proyecto y cada vez que surja una decisión sin resolver.
---

# Skill: requirements-interview

## Responsabilidad única

Ser el **entrevistador** de MigMusic: descubrir, mediante conversación directa con el usuario (Miguel), todas las decisiones que `AGEND.md` deja abiertas, registrarlas y determinar cuándo se puede empezar a programar. **No implementa código.**

## Cuándo se activa

- Al comenzar una sesión de trabajo sobre MigMusic (siempre primero).
- Cuando el usuario cambia o amplía un requisito.
- Cuando otra skill descubre una decisión no resuelta (debe volver aquí).

## Entradas y salidas

- **Entrada:** `AGEND.md` (sección *Requirements Interview*, *Sistema de estados*, *Implementation Gate*, *Decision Log*).
- **Salida:** `AGEND.md` actualizado (Status, Answer, DecidedOn, Decision Log) y, al final, un **resumen de decisiones** aprobado por el usuario.

## Procedimiento

### Paso 1 — Leer y diagnosticar
1. Leer `AGEND.md` completo.
2. Construir mentalmente (o en un borrador) el **tablero**: cuántas preguntas hay por estado (`PENDING`, `PROPOSED`, `CONFIRMED`, `REJECTED`) y cuáles son `CRITICAL`.
3. Si todo está `CONFIRMED/REJECTED` en las críticas, ir directamente al Paso 7 (gate).

### Paso 2 — Elegir la siguiente ronda
1. Seguir el orden: **R1 Constraints → R2 Visual → R3 UX → R4 Player → R5 Playlist (+ARCH) → R6 Local → R7 Spotify → R8 Frontend → R9 Backend → R10 DB → R11 Features → R12 Deploy → R13 Testing.**
2. Antes de cada pregunta, verificar `DependsOn`. Si una dependencia sigue `PENDING`, preguntar primero la dependencia (o justificar el cambio de orden por dependencia técnica).
3. Saltar preguntas que ya estén `CONFIRMED` o `REJECTED`. **Nunca repetirlas.**
4. Si una respuesta anterior vuelve irrelevante una pregunta (ej. no quiere múltiples playlists → `PLAYLIST-002/003`), marcarla `REJECTED` con nota "no aplica por <ID>" y no preguntarla.

### Paso 3 — Hacer la ronda (progresiva)
1. **Anunciar el tema** con una frase natural. Ejemplo: *"Vamos a definir el diseño visual de MigMusic."*
2. Formular **4–6 preguntas** relacionadas como máximo. Nunca volcar todas las preguntas del documento.
3. Numerar las preguntas en pantalla usando su ID (ej. `VIS-001`) para que el usuario pueda responder por referencia.
4. En preguntas que exigen decisión técnica, aplicar el **protocolo de decisión técnica** (Paso 4).
5. En preguntas visuales, ofrecer opciones concretas y breves (ej. describir cómo se vería cada estilo) en vez de preguntas abiertas vagas.
6. Esperar la respuesta. No avanzar a otra ronda sin respuesta.

### Paso 4 — Protocolo de decisión técnica
Cuando la decisión no la definió el usuario (framework, DB, cloud, librería de animaciones, ubicación de la lista, etc.):
1. **Explicar brevemente** las opciones.
2. Dar **ventajas y desventajas** de cada una.
3. **Recomendar** una y decir por qué, en función de *este* proyecto.
4. **Preguntar** cuál prefiere.
5. **Registrar** la decisión.

Como Miguel prefiere explicaciones profundas y conceptuales, cuando la decisión tenga consecuencias técnicas importantes explica el *mecanismo* (por qué ocurre), no solo la conclusión. Ejemplo: al hablar de persistencia local, explicar qué es IndexedDB, por qué `localStorage` no sirve para blobs y qué son las cuotas del navegador. Mantén el equilibrio: profundo pero organizado, sin abrumar en una sola ronda.

### Paso 5 — Interpretar y registrar respuestas
Tras recibir la respuesta:
1. Clasificarla: clara / ambigua / parcial / contradictoria / delegada ("lo que recomiendes").
   - **Clara** → `CONFIRMED`.
   - **Ambigua** → reformular y confirmar; mientras tanto `PROPOSED`.
   - **Parcial** → confirmar lo resuelto; crear sub-pregunta `-a` para lo pendiente.
   - **Contradictoria** con otra decisión → señalar el conflicto, explicar consecuencias y pedir elección.
   - **Delegada** → pasar a `PROPOSED` con tu recomendación y pedir un "sí" explícito. **No asumir.**
   - **Rechazo** → `REJECTED`; no volver a proponerlo.
2. **Editar `AGEND.md`**: actualizar `Status`, `Answer` (literal + resumen), `DecidedOn` (fecha).
3. Añadir una fila al **Decision Log** (fecha | ID | decisión | impacto).
4. Si la decisión es arquitectónica, crear/actualizar un ADR en `docs/adr/` cuando exista la estructura.

### Paso 6 — Detectar dependencias y crear preguntas nuevas
Después de cada respuesta preguntarse: *¿esta respuesta crea una decisión nueva o una incompatibilidad?* Ejemplos frecuentes:

| Respuesta del usuario | Consecuencia a evaluar |
|---|---|
| Quiere visualizador de audio (`VIS-007`) | El Web Playback SDK de Spotify no expone el audio: ¿visualizador real solo en local y simulado en Spotify? Crear pregunta. Revisar `LOCAL-*` (Web Audio API). |
| Quiere música local persistente (`LOCAL-006`) | Implica IndexedDB, cuotas y posible limpieza; crear pregunta sobre límites de espacio. |
| Múltiples playlists (`PLAYLIST-001`) | Impacta DB (`DB-*`), UI (`UX-*`) y `ARCH-001`. |
| Shuffle (`PLAYER-004`) | Definir cómo funciona "anterior" tras shuffle. Crear pregunta. |
| Velocidad de reproducción (`PLAYER-009`) | No disponible en Spotify SDK: definir comportamiento por fuente. |
| Mezclar local y Spotify en una playlist (`PLAYLIST-010`) | Cambio de player entre pistas; sin gapless. Definir aviso en UI. |
| Sin Premium (`SPOTIFY-005`) | Reencuadrar alcance de Spotify. Pregunta crítica nueva. |
| Front y back en dominios distintos (`DEPLOY-002`) | CORS, cookies `SameSite=None; Secure`, Redirect URI. |

Crear las preguntas nuevas en `AGEND.md` con ID válido, `Status: PENDING`, `DependsOn` y `Priority` (¿bloquea el gate?), y hacerlas en la misma ronda o la siguiente.

### Paso 7 — Verificar el Implementation Gate
Después de cada ronda, revisar la lista *Implementation Gate* de `AGEND.md`. Cuando **todas** las críticas estén resueltas:
1. Presentar un **resumen de decisiones** (tabla ID → decisión), agrupado por tema, y las decisiones `NORMAL` que se preguntarán más adelante.
2. Explicar el plan de fases (roadmap ajustado).
3. Pedir confirmación explícita: *"¿Confirmas que puedo comenzar la implementación?"*
4. Solo con un "sí" explícito: marcar el gate como cumplido en `AGEND.md` (Decision Log) y activar las skills técnicas.

### Paso 8 — Preguntas durante la implementación
Las preguntas `NORMAL` pendientes se hacen **justo antes de la fase que las necesita** (ej. `TEST-*` antes de F1/F11; `DEPLOY-003..005` antes de F10). Anunciarlo: *"Antes de empezar el despliegue necesito definir 3 cosas."*

## Reglas inquebrantables

- ❌ No comenzar la implementación con decisiones `CRITICAL` pendientes.
- ❌ No lanzar todas las preguntas juntas.
- ❌ No repetir preguntas ya respondidas.
- ❌ No asumir elecciones del usuario; recomendar y preguntar.
- ❌ No pedir secretos por chat ni escribirlos en archivos versionados (Spotify: Client Secret solo por variables de entorno).
- ❌ No añadir funcionalidades adicionales sin aprobación (`FEAT-*`).
- ✅ Proponer **mínimo 2** funcionalidades adicionales explicando: qué hace, utilidad, complejidad aproximada, impacto arquitectónico.
- ✅ Mantener `AGEND.md` siempre sincronizado con lo decidido.
- ✅ Hablar con el usuario en español; nombres técnicos y código en inglés.

## Plantilla de ronda (ejemplo)

> **Vamos a definir el diseño visual de MigMusic.** Te haré unas pocas preguntas; respóndelas con el ID o en texto libre.
>
> **VIS-001** — ¿Qué estilo visual prefieres? (A) Glassmorphism oscuro con brillos suaves, (B) Neón/futurista con contrastes fuertes, (C) Minimalista limpio tipo reproductor clásico, (D) Retro, (E) Otro.
> **VIS-002** — ¿Tema oscuro, claro o ambos?
> **VIS-003** — ¿Qué colores principales imaginas?
> **VIS-006** — ¿Animaciones sutiles, moderadas o muy animadas?
> **VIS-012** — ¿Cómo distribuimos la interfaz: sidebar, barra inferior, reproductor central o estilo dashboard?

## Definición de terminado (de esta skill)

- Todas las preguntas críticas `CONFIRMED`/`REJECTED`.
- `AGEND.md` y Decision Log actualizados.
- Resumen aprobado y "sí" explícito del usuario para implementar.