---
name: doubly-linked-list
description: Implementa, prueba y explica la lista doblemente enlazada real (Node + DoublyLinkedList) que sustenta la playlist de MigMusic, con invariantes, casos borde, complejidades y guion pedagógico. Úsala al construir el dominio de playlist.
---

# Skill: doubly-linked-list

## Responsabilidad única

Producir una **lista doblemente enlazada auténtica** (nodos con `previous` y `next`), integrarla en `Playlist`, probarla exhaustivamente y ser capaz de **explicarla** al usuario. Es el núcleo académico del proyecto.

## Precondiciones (AGEND.md)

`ARCH-001` (dónde vive), `PLAYLIST-009` (extremos: detenerse o circular), `PLAYLIST-001`, y `backend-architecture-python` aplicado (capa `domain/structures`).

## Especificación

```
Node
- song        : Song
- previous    : Node | None
- next        : Node | None

DoublyLinkedList
- head        : Node | None
- tail        : Node | None
- current     : Node | None
- size        : int
```

### Operaciones mínimas

| Operación (concepto) | Python (snake_case) | Comportamiento | Complejidad |
|---|---|---|---|
| insertAtBeginning | `insert_at_beginning(song)` | Nuevo nodo pasa a ser `head`. Si la lista estaba vacía, también `tail` y `current`. | O(1) |
| insertAtEnd | `insert_at_end(song)` | Nuevo nodo pasa a ser `tail`. | O(1) |
| insertAt | `insert_at(position, song)` | Inserta en índice 0..size. 0 delega a beginning; size delega a end; intermedio recorre desde el extremo más cercano. Fuera de rango → `InvalidPositionError`. | O(n) |
| remove | `remove(song_or_node)` | Elimina por referencia/valor; reenlaza vecinos; actualiza head/tail/current. | O(n) por búsqueda; O(1) si se recibe el nodo |
| removeAt | `remove_at(position)` | Elimina por índice; devuelve la canción eliminada. | O(n) |
| find | `find(predicate_or_song)` | Devuelve el nodo/posición o `None`. | O(n) |
| moveNext | `move_next()` | `current = current.next`; en `tail` aplica política de extremos. | O(1) |
| movePrevious | `move_previous()` | `current = current.previous`; en `head` aplica política de extremos. | O(1) |
| getCurrent | `get_current()` | Devuelve la canción actual o lanza/retorna vacío según diseño. | O(1) |
| getSize | `get_size()` | Devuelve `size`. | O(1) |
| clear | `clear()` | Deja head/tail/current en `None` y size en 0 (desenlazar nodos para ayudar al GC). | O(n) |

Adicionales recomendados: `is_empty()`, `move_to(position)` / `set_current(node)` (seleccionar canción de la UI), `to_list()` (**solo para serializar/mostrar**, nunca como almacenamiento), iterador `__iter__`, `__len__`.

### Invariantes (verificar en tests y, en desarrollo, con un método `_assert_invariants()`)

1. `size == 0` ⟺ `head is None` ⟺ `tail is None` ⟺ `current is None`.
2. `head.previous is None` y `tail.next is None` (salvo política circular, que debe documentarse y cambiar el invariante de forma consistente).
3. Para todo nodo `n` con `n.next`, se cumple `n.next.previous is n`.
4. Recorriendo desde `head` por `next` se visitan exactamente `size` nodos y se termina en `tail`.
5. `current`, si no es `None`, pertenece a la lista.

### Política de extremos (`PLAYLIST-009`)

- **Detenerse:** `move_next()` en `tail` no cambia `current` y señala fin (excepción `EndOfPlaylistError` o valor de retorno booleano; definir y documentar).
- **Circular:** decidir si se implementa enlazando `tail.next = head` (cambia invariantes) o en la capa de servicio (`PlaybackService` envuelve al llegar al extremo) manteniendo la lista pura. **Recomendación:** mantener la lista pura y resolver la circularidad en la capa de servicio/`Playlist`, para conservar la definición clásica.

## Reglas de implementación

- ❌ Prohibido `list`/`Array` como almacenamiento interno. Está permitido convertir a lista **únicamente** para serializar (DTO) o pruebas.
- ✅ Encapsulación: `head`, `tail`, `current`, `size` de solo lectura hacia fuera (propiedades). Los nodos son detalle interno; la API pública opera sobre `Song`/posiciones.
- ✅ Genérica si es posible (`Generic[T]`) o tipada con `Song`.
- ✅ Errores de dominio explícitos: `EmptyPlaylistError`, `InvalidPositionError`.
- ✅ Docstring de cada método con complejidad en O().
- ✅ Optimización de `insert_at`/`remove_at`: recorrer desde `head` si `position < size/2`, si no desde `tail` (aprovecha la doble dirección — buen punto para explicar).
- ✅ Manejar explícitamente qué pasa con `current` al eliminar el nodo actual (recomendado: pasar a `next`, o a `previous` si era `tail`; documentarlo y confirmar con el usuario si afecta a la UX).

## Integración en `Playlist`

- `Playlist` **contiene** una `DoublyLinkedList` (composición) y añade reglas propias: nombre, duplicados (si se decide), modos repeat/shuffle (si se aprueban).
- Shuffle/historial **no deben romper** la lista: implementar como estrategia en el servicio (p. ej. `PlaybackStrategy` con `SequentialStrategy`, `ShuffleStrategy`, `RepeatOneStrategy`), no alterando nodos innecesariamente.
- Cambio de fuente (local ↔ Spotify) lo resuelve el player, no la lista; la lista solo conoce `Song` y su `AudioSourceType`.

## Estrategia de pruebas (mínimo)

Para cada operación:
- Lista vacía · un elemento · dos elementos · varios.
- Inserción/eliminación en cabeza, cola, medio.
- Posiciones inválidas (negativas, > size).
- Eliminar `current` (cabeza, cola, medio, único).
- `move_next`/`move_previous` en extremos según política.
- Invariantes tras **cada** operación (test parametrizado o property-based con `hypothesis`, si se acepta).
- Secuencias mixtas aleatorias contrastadas con un modelo de referencia simple (un `list` en el **test**, no en el código de producción).
- `clear` y reutilización posterior.

Si `ARCH-001 = C` (backend y frontend): crear un **archivo de casos de contrato** (JSON con operaciones y estado esperado) consumido por los tests de ambos lenguajes.

## Guion para explicar la lista al usuario (obligatorio saber hacerlo)

Cuando Miguel pida "explícame cómo funciona", cubrir en este orden:
1. **Idea:** cada canción vive en un nodo que sabe quién viene antes y después.
2. **Por qué doble enlace:** permite retroceder en O(1) (botón Previous) y eliminar un nodo conocido sin recorrer desde el inicio.
3. **Dibujo ASCII** de `head ⇄ A ⇄ B ⇄ C ⇄ tail`, con `current` marcado.
4. **Paso a paso** de `insert_at(1, X)`: crear nodo → apuntar `X.previous = A`, `X.next = B` → `A.next = X` → `B.previous = X` → `size += 1` (el orden evita perder referencias).
5. **Paso a paso** de `remove` del nodo `B`: `B.previous.next = B.next`, `B.next.previous = B.previous`, corregir head/tail/current.
6. **Comparación** con array: inserciones O(1) en extremos y sin desplazar elementos; coste: acceso por índice O(n) y más memoria por punteros.
7. **Conexión con MigMusic:** Next = `move_next()`, Previous = `move_previous()`, fin de canción = `move_next()`, agregar/eliminar desde la UI = operaciones de la lista.

Cuando exista la vista didáctica (`UX-002`), el agente debe cablearla a los eventos de la lista para que las flechas se animen al insertar/eliminar.

## Definición de terminado

- [ ] Todas las operaciones mínimas implementadas con nodos reales.
- [ ] Invariantes verificados; cobertura acorde a `TEST-002` (recomendado ≥ 95 % en esta clase).
- [ ] Docstrings con complejidades.
- [ ] `Playlist` usa la lista; ningún array como sustituto.
- [ ] El agente puede explicar la estructura con el guion anterior.