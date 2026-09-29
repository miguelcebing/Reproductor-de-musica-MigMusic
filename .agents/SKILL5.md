---
name: ui-ux-design
description: Construye la interfaz funcional, moderna, animada, accesible y responsive de MigMusic con arquitectura frontend orientada a objetos, design tokens y separación UI/lógica. Úsala tras confirmar VIS-*, UX-* y FRONT-*.
---

# Skill: ui-ux-design

## Responsabilidad única

Diseñar e implementar la **capa de presentación** del frontend: layout, componentes, estilos, animaciones, responsive y accesibilidad, conectándola a los controladores/servicios. **No** contiene reglas de negocio ni lógica de audio (eso vive en `players/` y `services/`).

## Precondiciones (AGEND.md)

`VIS-001`, `VIS-006`, `VIS-012` (críticas) y el resto de `VIS-*`/`UX-*` relevantes; `FRONT-001`, `FRONT-002`, `FRONT-003..006`.

## Principios

1. **La interfaz NO es un mockup.** Cada control principal está conectado a lógica real: Play, Pause, Next, Previous, Seek, Volume, Mute, Adelantar (N s), Retroceder (N s), Agregar canción, Eliminar canción, Seleccionar canción.
2. **Separación estricta:** componentes presentacionales (reciben props/eventos) ↔ controladores/servicios (`PlaybackController`, `PlaylistController`, `ApiClient`) ↔ players (`AudioPlayer`).
3. **POO en el frontend:** la lógica de aplicación en clases (controladores, players, repositorios, validadores); los componentes solo orquestan la vista. Con TypeScript (si `FRONT-002`): interfaces y clases abstractas, `readonly`, modificadores de acceso.
4. **Inglés en el código** (nombres de componentes, props, clases CSS, tipos). Los textos visibles siguen `CONS-006`.

## Estructura (dentro de `frontend/src`)

```
domain/        Song, AudioSourceType, DoublyLinkedList (si ARCH-001 = B o C)
players/       AudioPlayer (abstracto), LocalAudioPlayer, SpotifyPlayer, PlayerFactory
services/      ApiClient, PlaybackController, PlaylistController, AuthController
storage/       LocalLibraryRepository (si aplica)
state/         store/estado observable (según FRONT-005), sin lógica de negocio compleja
ui/
  components/  PlayerControls, ProgressBar, VolumeControl, TrackList, TrackItem,
               AddTrackDialog, CoverArt, NowPlaying, LinkedListView (si UX-002), Toast...
  layouts/     AppShell, Sidebar/BottomBar/Dashboard (según VIS-012)
  animations/  presets reutilizables (según FRONT-003/004)
styles/        tokens (color, tipografía, espaciado, radios, sombras, motion), temas, reset
```

## Design tokens y temas

- Definir tokens (CSS variables): colores (`VIS-003/004`), gradientes (`VIS-005`), espaciado, radios, sombras, duraciones y easings.
- Temas (`VIS-002`): claro/oscuro/ambos vía `data-theme` y `prefers-color-scheme`.
- Contraste mínimo WCAG AA para texto y controles.
- Tipografía: proponer 1–2 fuentes acordes al estilo (`VIS-001`) y confirmar; cargar con `font-display: swap`.

## Animaciones (según `VIS-006`, `FRONT-003/004`)

| Nivel | Contenido típico |
|---|---|
| Sutil | Transiciones de hover/focus, fade de cambio de pista, barra de progreso suave. |
| Moderado | + rotación/pulso de portada, transición de fondo/gradiente al cambiar canción, microinteracciones en botones. |
| Muy animado | + visualizador, partículas/blur dinámico, transiciones de layout, animación de nodos enlazados. |

Reglas:
- Animar solo `transform` y `opacity` siempre que se pueda (GPU); evitar layout thrashing.
- Respetar `prefers-reduced-motion`: reducir/desactivar animaciones y ofrecer ajuste en la UI.
- Presupuesto de rendimiento en móvil: 60 fps objetivo; degradar visualizador/efectos en dispositivos lentos.
- Visualizador/ondas (`VIS-007/008`): solo real con audio local (Web Audio); en Spotify, si el usuario lo acepta, una animación **sintetizada** claramente diferenciada (no fingir que es el audio real).
- Vista didáctica de nodos (`UX-002`): representar `head ⇄ … ⇄ tail`, resaltar `current`, animar inserción/eliminación reenlazando flechas.

## Layout y responsive (`VIS-012`, `FRONT-006`)

Mobile-first con rangos (confirmar valores):
- **Mobile** (< ~640 px): una columna, reproductor mini fijo abajo con expansión a pantalla completa, lista en hoja/pestaña, controles con área táctil ≥ 44 px.
- **Tablet** (~640–1024 px): dos zonas (lista + reproductor), sidebar colapsable.
- **Laptop** (~1024–1440 px): layout completo.
- **Desktop** (> ~1440 px): ancho máximo contenido, tipografía y portada escaladas, opcionalmente panel extra (cola/nodos).

Verificar con dispositivos reales o emulación: orientación vertical/horizontal, zonas seguras (notch), teclado virtual, scroll de lista larga (virtualización si hay cientos de pistas).

## Componentes clave y comportamiento

- **PlayerControls:** play/pause (estado reflejado), previous, next, retroceder N s, adelantar N s (etiquetas con el valor de N), shuffle/repeat si están aprobados. Deshabilitar con estado claro cuando la lista está vacía o en extremo sin repeat.
- **ProgressBar:** interactiva (click, arrastre, teclado con flechas), muestra tiempo actual/total, buffered si aplica; usa `seekTo`.
- **VolumeControl:** slider + mute; recuerda el valor.
- **TrackList/TrackItem:** indica pista actual, fuente (icono local/Spotify), acciones (reproducir, eliminar, mover si se aprobó drag and drop), estados vacío/cargando/error.
- **AddTrackDialog:** elegir origen (archivo local / búsqueda Spotify) y **posición** (inicio, final, índice N); validación visible.
- **Estados globales:** vacío (invitar a agregar música), sin conexión, Spotify no conectado/sin Premium, error de reproducción.

## Accesibilidad

- Elementos semánticos (`button`, `nav`, `main`), no `div` clicables.
- `aria-label` en botones de icono, `aria-pressed` en toggles, `role="slider"` con `aria-valuenow/min/max/text` en progreso y volumen si son personalizados.
- Foco visible y orden lógico; atajos de teclado (`PLAYER-010`) sin conflictos con inputs; desactivables.
- `aria-live="polite"` para "Reproduciendo: título — artista".
- Contraste y tamaños táctiles adecuados.

## Rendimiento

- Code-splitting: cargar el SDK de Spotify y el lector de metadata bajo demanda.
- Imágenes/portadas con dimensiones fijas, `loading="lazy"`, `decoding="async"`.
- Evitar rerenders masivos en `timeupdate` (throttle a ~4–10 Hz para texto; la barra puede usar rAF).

## Pruebas

- Componentes: render, estados, eventos (Testing Library o equivalente).
- Accesibilidad automática (axe) en vistas principales.
- E2E responsive (Playwright con viewports mobile/tablet/desktop).
- Revisión visual manual con la checklist de `VIS-*` confirmadas.

## Definición de terminado

- [ ] Todos los controles principales funcionan de verdad con ambas fuentes.
- [ ] Estilo, tema, colores, animaciones y layout coinciden con las decisiones `CONFIRMED`.
- [ ] Responsive verificado en 4 categorías de dispositivo.
- [ ] `prefers-reduced-motion` y accesibilidad de teclado implementados.
- [ ] Sin lógica de negocio dentro de componentes.
- [ ] Código, clases y componentes en inglés.