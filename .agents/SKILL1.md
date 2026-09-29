---
name: backend-architecture-python
description: Reglas para construir el backend 100% Python de MigMusic con POO, arquitectura por capas (domain/application/infrastructure/api), SOLID e inyección de dependencias, con estructura de carpetas claramente separada. Úsala al iniciar y en cada revisión del backend.
---

# Skill: backend-architecture-python

## Responsabilidad única

Garantizar que **todo el backend está escrito en Python**, sigue **Programación Orientada a Objetos** y tiene una **estructura organizada y separada** que evidencia buena arquitectura. No define la lista enlazada (`doubly-linked-list`), ni Spotify (`spotify-integration`), ni el despliegue (`deployment-cloud`); las *aloja* correctamente.

## Precondiciones (deben estar `CONFIRMED` en AGEND.md)

`ARCH-001`, `ARCH-002`, `BACK-001` (framework), `BACK-002`, `DB-001` (y `DB-002/003` si hay base de datos), Implementation Gate cumplido.

## Reglas de arquitectura

### 1. Capas y dirección de dependencias
```
api  ──▶  application  ──▶  domain  ◀──  infrastructure
                              ▲
                     core (config, logging, errores base)
```
- `domain`: **cero** imports de framework, HTTP, ORM, Spotify ni `os.environ`. Solo Python estándar y tipos.
- `application`: casos de uso; depende de `domain` y de **puertos** (ABC), nunca de implementaciones concretas.
- `infrastructure`: implementa los puertos (Spotify, repositorios, almacén de tokens).
- `api`: rutas delgadas; solo traduce HTTP ↔ DTO ↔ caso de uso.
- `main.py` es el **composition root**: único sitio donde se instancian implementaciones concretas y se inyectan.
- Prohibidos los imports circulares y los imports "hacia arriba".

### 2. POO obligatoria
- **Encapsulación:** atributos privados (`_name`) y acceso mediante métodos/propiedades; el estado de `DoublyLinkedList` solo se modifica por sus métodos.
- **Abstracción:** puertos como `abc.ABC` con `@abstractmethod` (o `typing.Protocol` si se justifica): `PlaylistRepository`, `MusicProvider`, `TokenStore`.
- **Polimorfismo:** varias implementaciones tras un mismo puerto (`InMemoryPlaylistRepository` / `SqlPlaylistRepository`).
- **Composición sobre herencia:** heredar solo para contratos; compartir comportamiento por composición.
- **Sin funciones sueltas de negocio:** la lógica vive en clases (los helpers puramente técnicos van en `core/` o módulos de utilidad pequeños y justificados).
- **Value Objects** inmutables (`@dataclass(frozen=True)`) para `Song` cuando aplique.

### 3. SOLID (verificable en revisión)
| Principio | Cómo se comprueba |
|---|---|
| S | Cada clase tiene una razón para cambiar; `PlaylistService` no habla con Spotify. |
| O | Añadir una nueva fuente (ej. YouTube) = nueva clase `MusicProvider`, sin tocar servicios. |
| L | Cualquier `PlaylistRepository` es intercambiable sin romper servicios. |
| I | Puertos pequeños y específicos (no un "GodRepository"). |
| D | Servicios reciben puertos por constructor; no instancian infraestructura. |

### 4. Calidad de código
- **Type hints en todo** y verificación con `mypy` (modo estricto para `domain` y `application`).
- Formato/lint: `ruff` + `black` (según `BACK-003`).
- **Docstrings** en clases y métodos públicos; comentarios técnicos **en inglés**.
- Nombres en inglés: clases `PascalCase`, funciones/variables `snake_case`, constantes `UPPER_SNAKE_CASE`.
- Excepciones de dominio propias (`EmptyPlaylistError`, `InvalidPositionError`, `SongNotFoundError`); las rutas no capturan excepciones genéricas: un único `error_handlers.py` las traduce a HTTP.
- Configuración con una clase `Settings` que lee variables de entorno y **falla al arrancar** si falta una obligatoria.
- Logging estructurado sin datos sensibles.

### 5. Estructura de carpetas (obligatoria; ajustar nombres solo vía ARCH-002)
Ver árbol en la sección 8.2 de `AGEND.md`. Reglas de organización:
- Un concepto por archivo; nombres de archivo en `snake_case` que reflejan la clase principal.
- Cada carpeta tiene `__init__.py` que expone solo su API pública.
- Tests en `tests/` espejando la estructura de `src/`.
- Nada de "utils.py" cajón de sastre. Si algo no tiene hogar claro, se revisa el diseño.
- `docs/adr/` contiene un ADR por decisión arquitectónica importante.

## Procedimiento

1. **Scaffold:** crear el árbol de carpetas vacío con `__init__.py`, `pyproject.toml`, `.env.example`, `.gitignore` (incluye `.env`).
2. **Core:** `Settings`, logging, excepciones base.
3. **Domain primero** (con `doubly-linked-list`): entidades, estructura, puertos, excepciones. Con tests antes de continuar (idealmente TDD).
4. **Application:** servicios inyectando puertos.
5. **Infrastructure:** adaptadores; empezar por `InMemoryPlaylistRepository`.
6. **API:** schemas, routers delgados, dependencias, manejo de errores.
7. **Composition root:** cablear en `main.py`.
8. **Revisión arquitectónica** (checklist abajo) antes de dar por cerrada cada fase.

## Checklist de revisión (bloquea el cierre de fase)

- [ ] ¿Algún archivo de `domain/` importa FastAPI/Flask/Django/SQLAlchemy/requests/os.environ? (debe ser **no**)
- [ ] ¿Algún router contiene lógica de negocio? (debe ser **no**)
- [ ] ¿Los servicios reciben dependencias por constructor? (debe ser **sí**)
- [ ] ¿Hay clases abstractas para cada puerto? (**sí**)
- [ ] ¿Hay type hints y `mypy` pasa? (**sí**)
- [ ] ¿Los nombres y comentarios están en inglés? (**sí**)
- [ ] ¿Existe algún secreto en el repositorio? (debe ser **no**)
- [ ] ¿Cada capa tiene tests? (**sí**)
- [ ] ¿La estructura de carpetas coincide con `AGEND.md`/ADR? (**sí**)

## Antipatrones a evitar

- Rutas que llaman directamente a Spotify o a la base de datos.
- Entidades de dominio con decoradores de ORM o de Pydantic del framework.
- Variables globales de estado (usar servicios y repositorios inyectados).
- Estado de reproducción "en la ruta". Debe vivir en `PlaybackService`/repositorio.
- Duplicar reglas de negocio en API y servicios.

## Notas por framework (según BACK-001)

- **FastAPI:** `Depends` para inyección; routers por recurso; Pydantic solo en `api/schemas`.
- **Flask:** Blueprints por recurso + application factory (`create_app`); un contenedor sencillo de dependencias.
- **Django:** mantener el dominio fuera de `models.py`; los modelos Django son detalle de `infrastructure` y un repositorio adapta a entidades de dominio.