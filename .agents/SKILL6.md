---
name: testing-quality
description: Define y ejecuta la estrategia de pruebas y calidad de MigMusic (unitarias, integración, contrato de la lista, e2e, accesibilidad, manuales) con pytest en Python y herramientas de frontend. Úsala de forma continua y antes de cerrar cada fase.
---

# Skill: testing-quality

## Responsabilidad única

Asegurar que cada entregable está **probado y cumple criterios de calidad** antes de darse por terminado. No decide el diseño; verifica que se cumple lo decidido en `AGEND.md`.

## Precondiciones (AGEND.md)

`TEST-001..003` (se preguntan antes de F1; si siguen `PENDING` al iniciar F1, aplicar `requirements-interview` Paso 8). Al final de cada fase, este skill se aplica **siempre**.

## Pirámide de pruebas

| Nivel | Objetivo | Herramientas sugeridas (confirmar en `TEST-001`) |
|---|---|---|
| **Unitarias (base, mayoría)** | Dominio y servicios aislados, rápidos, sin red ni disco. | `pytest`, `pytest-cov`; `Vitest`/`Jest` en frontend |
| **Contrato** | Misma semántica de la lista en Python y frontend (si `ARCH-001 = C`). | Casos JSON compartidos |
| **Integración** | API + adaptadores con dobles de Spotify y repositorio real/in-memory. | `pytest` + `httpx`/`TestClient`, `respx` |
| **Componentes UI** | Vistas y eventos. | Testing Library |
| **E2E (pocas, críticas)** | Flujos completos en navegador real. | Playwright (o Cypress) |
| **Accesibilidad** | Reglas automáticas WCAG básicas. | `axe` |
| **Manuales guiados** | Spotify real, dispositivos móviles, navegadores. | Checklist |

## Objetivos de cobertura (propuesta, confirmar en `TEST-002`)

- `DoublyLinkedList`/`Playlist`: ≥ 95 % de líneas y ramas.
- `domain` + `application`: ≥ 90 %.
- `infrastructure`/`api`: ≥ 80 %.
- Frontend (controladores/players): ≥ 80 %.
La cobertura es indicador, no meta: priorizar casos borde reales.

## Qué probar (mínimos por área)

**Lista doblemente enlazada:** ver skill `doubly-linked-list` (vacía, uno, extremos, medio, posición inválida, eliminar `current`, invariantes, secuencias mixtas contra un modelo de referencia).

**Servicios:**
- `PlaylistService`: agregar en inicio/final/posición, eliminar, mover, búsqueda; errores de dominio.
- `PlaybackService`: next/previous con y sin repeat/shuffle, fin de lista, skip ± N s con límites (0 y duración), lista vacía.
- `SpotifyAuthService`: `state` inválido, código inválido, refresh exitoso/fallido, expiración concurrente.

**API:** códigos HTTP, validación de schemas, traducción de excepciones de dominio, CORS, cookies (`HttpOnly`, `Secure`, `SameSite`), rate limiting en `/auth/*`.

**Seguridad:** el Client Secret no aparece en respuestas, logs ni bundle (test que escanee el build y las respuestas); `.env` ignorado por git; tokens no se registran.

**Frontend:** `LocalAudioPlayer` (eventos), `SpotifyPlayer` (SDK simulado), `PlaybackController`, `LocalLibraryRepository` (`fake-indexeddb`), validador de archivos, cálculo de clamp del skip.

**E2E (flujo maestro):** agregar 3 canciones locales → reproducir → next → previous → skip adelante N s → skip atrás N s → seek en la barra → volumen/mute → insertar en posición 2 → eliminar la actual → verificar UI y estado. Repetir en viewport mobile.

**Manual guiado (Premium):** OAuth completo, reproducción, pausa, seek, skip, cambio local↔Spotify, expiración de token, cuenta sin Premium, revocar acceso desde Spotify, cerrar sesión.

## Prácticas

- **TDD recomendado** para dominio: test primero.
- Tests deterministas: sin dependencia de tiempo real (inyectar reloj), sin red, sin orden.
- Nombres descriptivos en inglés (`test_remove_current_node_moves_pointer_to_next`).
- Fixtures y factories reutilizables (`SongFactory`).
- Un fallo de prueba **bloquea** el cierre de fase.
- Análisis estático: `ruff`, `mypy` (backend), `eslint` + `tsc --noEmit` (frontend).
- Auditoría de dependencias (`pip-audit`, `npm audit`) en CI.

## CI (si `DEPLOY-003`/`TEST-003` confirmados)

Pipeline por PR: lint → type-check → unit → integración → build frontend → e2e (ligero) → reporte de cobertura. Despliegue solo si todo pasa.

## Puerta de calidad por fase

Antes de marcar una fase como terminada:
- [ ] Tests nuevos escritos y pasando.
- [ ] Cobertura no baja del umbral.
- [ ] Lint y type-check limpios.
- [ ] Checklist de arquitectura (`backend-architecture-python`) sin violaciones.
- [ ] Sin secretos ni datos sensibles.
- [ ] `AGEND.md` (criterios de aceptación relevantes, Decision Log) actualizado.

## Reporte final (F11)

Entregar tabla: criterio de aceptación → evidencia (test/captura/enlace) → estado. Documentar limitaciones conocidas (p. ej. Web Playback SDK en móviles) sin ocultarlas.