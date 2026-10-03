---
name: local-audio
description: Implementa la reproducción de música local en MigMusic (File Picker, drag and drop, HTML5 Audio/Web Audio, metadata, portadas, persistencia con IndexedDB, seek y skip de N segundos) con clases POO en el frontend. Úsala tras confirmar LOCAL-*.
---

# Skill: local-audio

## Responsabilidad única

Todo lo que tiene que ver con **archivos de audio del equipo del usuario**: selección, validación, lectura de metadata, reproducción, control y persistencia local. No toca Spotify (`spotify-integration`) ni la estructura de lista (`doubly-linked-list`).

## Precondiciones (AGEND.md)

`LOCAL-001`, `LOCAL-006` `CONFIRMED` (críticas); `LOCAL-002..005`, `LOCAL-007`, `LOCAL-008` según se hayan respondido; `FRONT-001/002`; `PLAYER-001/002` (segundos de skip).

## Principio de privacidad

Por defecto los archivos **permanecen en el navegador**; no se suben al servidor. Si el usuario desea procesar metadata en Python (p. ej. `mutagen`) o subir archivos, es una **decisión nueva** (crear pregunta, explicar implicaciones de privacidad, ancho de banda, almacenamiento y seguridad de subida) y no se asume.

## Diseño POO (frontend)

```
players/AudioPlayer.(ts)            # clase abstracta / interfaz común
players/LocalAudioPlayer.(ts)       # implementa AudioPlayer con HTMLAudioElement
library/LocalFileValidator          # valida extensión, MIME, tamaño
library/AudioMetadataReader         # extrae título/artista/álbum/duración/portada
library/LocalTrackFactory           # crea Song (source=LOCAL) desde File
storage/LocalLibraryRepository      # persistencia (IndexedDB) si se aprueba
storage/ObjectUrlRegistry           # crea y revoca object URLs
```

### Interfaz común `AudioPlayer` (contrato con Spotify)
`load(song)`, `play()`, `pause()`, `seekTo(seconds)`, `skipForward()`, `skipBackward()`, `setVolume(0..1)`, `mute()/unmute()`, `getCurrentTime()`, `getDuration()`, `onEnded(cb)`, `onTimeUpdate(cb)`, `onError(cb)`, `dispose()`.
`LocalAudioPlayer` y `SpotifyPlayer` la implementan: **polimorfismo** puro. La UI y los controladores dependen de la abstracción.

## Selección de archivos

- `<input type="file" accept="audio/*" multiple>` (multiple según `LOCAL-002`), accesible por teclado y móvil.
- **Drag and drop** solo si `LOCAL-003 = CONFIRMED`: zona con feedback visual; el File Picker sigue existiendo.
- Validación (`LocalFileValidator`): extensión en la lista de `LOCAL-001`, MIME `audio/*`, tamaño máximo razonable (proponer y confirmar), rechazo con mensaje claro. **No confiar solo en la extensión**: comprobar que el navegador puede reproducirlo (`audio.canPlayType(mime)` / evento `error` en la carga).
- Formatos: MP3 y WAV son universales; OGG/FLAC/AAC/M4A varían por navegador → advertir y ofrecer fallback (mensaje "formato no soportado en este navegador").
- Al agregar varios archivos, respetar el orden acordado (por selección o alfabético) y la posición elegida (inicio/final/índice) aplicando operaciones de la lista.

## Reproducción con HTML5 Audio

- Un `HTMLAudioElement` gestionado por `LocalAudioPlayer`. Fuente con `URL.createObjectURL(file)`.
- **Liberar memoria:** `URL.revokeObjectURL` al cambiar de pista, eliminar la canción y en `dispose()` (`ObjectUrlRegistry` centraliza esto).
- **Seek:** `audio.currentTime = clamp(t, 0, duration)`.
- **Skip forward / backward N segundos:** `seekTo(clamp(currentTime ± N, 0, duration))`. N viene de `PLAYER-001/002` (no hardcodear). Si adelantar supera la duración → tratar como fin de pista (`moveNext`). Si retroceder pasa de 0 → quedar en 0.
- **Fin de pista:** evento `ended` → aplicar `PLAYER-003/005/006` (autoplay, repeat one, repeat all) invocando la lista.
- Volumen `audio.volume`, mute `audio.muted`. Nota: en iOS el volumen lo controla el sistema (`volume` puede ser ignorado) → informar.
- Velocidad `audio.playbackRate` solo si `PLAYER-009` confirmado (aplicar `preservesPitch`).
- Autoplay: los navegadores bloquean audio sin gesto del usuario; la primera reproducción debe originarse de un clic/tap. Manejar la promesa de `play()` y su rechazo.
- Media Session API (opcional pero recomendable): metadatos y controles del sistema (bloqueo de pantalla, teclas multimedia).
- Manejo de errores del elemento (`MediaError`): archivo corrupto, formato no soportado → mensaje UX y saltar a la siguiente pista si aplica.

## Metadata y portadas (`LOCAL-004`, `LOCAL-005`)

- Lectura en el navegador de etiquetas ID3/Vorbis/MP4 con una librería adecuada (evaluar y recomendar según `FRONT-001`; explicar el tamaño de bundle).
- Fallbacks: si falta título → nombre de archivo sin extensión; si falta duración → leer `loadedmetadata`.
- Portada extraída (blob) → object URL con su ciclo de vida gestionado; portada por defecto si no hay.
- Extraer metadata **antes** de crear el `Song`; el `Song` resultante es inmutable.

## Persistencia (`LOCAL-006`, `LOCAL-007`, `LOCAL-008`)

Explicar al usuario, antes de implementar, las tres estrategias y su implicación:

| Estrategia | Qué guarda | Ventaja | Desventaja |
|---|---|---|---|
| Sin persistencia | Nada | Simple, sin cuotas | Se pierde al cerrar |
| Solo metadatos | Lista y datos | Ligera | Hay que volver a seleccionar los archivos |
| **IndexedDB con blobs** | Archivos completos | Persistencia real offline | Ocupa disco, cuotas variables del navegador, puede ser purgado |

Si se elige IndexedDB:
- `LocalLibraryRepository` encapsula la API (una clase, sin IndexedDB "suelto" en la UI); versionado del esquema y migraciones.
- Guardar blob + metadata + posición/orden de la playlist (el orden se puede reconstruir en la lista enlazada al cargar).
- Consultar `navigator.storage.estimate()` y avisar cuando falte espacio; `navigator.storage.persist()` opcional.
- Operaciones asíncronas con manejo de errores (cuota excedida, modo privado).
- Botón "Borrar biblioteca local" y borrado de un solo elemento al eliminar la canción.
- `localStorage` **no** es válido para blobs (solo preferencias pequeñas).
- File System Access API: solo si se elige explícitamente, con fallback (no está en todos los navegadores).

## Integración con la lista

- Agregar archivo → crear `Song` → `insert_at_beginning/insert_at_end/insert_at` de la playlist.
- Eliminar canción → `remove/remove_at` + liberar object URL + borrar de IndexedDB si aplica.
- Seleccionar canción → posicionar `current` y cargar en `LocalAudioPlayer`.
- Cambiar entre pista local y de Spotify → el `PlayerFactory` entrega el `AudioPlayer` correcto; el anterior se pausa.

## Visualizador / ecualizador (solo si se aprueban)

- Requieren **Web Audio API** (`AudioContext`, `MediaElementAudioSourceNode`, `AnalyserNode`, `BiquadFilterNode`). El audio local sí lo permite; Spotify SDK no.
- Encapsular en `AudioAnalyser` (clase) y desacoplar de la UI (emite datos de frecuencia por callback).
- Reanudar `AudioContext` tras un gesto del usuario.

## Accesibilidad

Botones nativos, `aria-label`, foco visible, estados anunciados (`aria-live` para "Reproduciendo: …"), soporte de teclado según `PLAYER-010`.

## Pruebas

- **Unitarias:** `LocalFileValidator`, `LocalTrackFactory`, `ObjectUrlRegistry`, cálculo de skip con clamp (casos: inicio, final, N mayor que duración), `LocalLibraryRepository` con `fake-indexeddb`.
- **Componentes/integración:** `LocalAudioPlayer` con `HTMLAudioElement` simulado (eventos `ended`, `timeupdate`, `error`).
- **E2E:** subir 3 archivos de prueba (MP3 y WAV pequeños) → reproducir → next/prev → skip ± N → eliminar → recargar (si hay persistencia).
- **Manual:** Chrome, Firefox, Safari, móvil (iOS/Android).

## Definición de terminado

- [ ] Selección (y drag and drop si se aprobó) de archivos con validación.
- [ ] Reproducir, pausar, seek, skip ± N s (N configurado), volumen/mute, siguiente/anterior, eliminar.
- [ ] Sin fugas de object URLs.
- [ ] Persistencia según lo decidido y probada.
- [ ] Errores manejados con mensajes claros.
- [ ] `LocalAudioPlayer` intercambiable con `SpotifyPlayer` por la misma interfaz.