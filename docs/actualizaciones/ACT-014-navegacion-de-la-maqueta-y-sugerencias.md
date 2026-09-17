# ACT-014 — Navegación de la maqueta, sugerencias al escribir y la mascota

| Campo | Valor |
|---|---|
| Fecha | 2026-09-17 |
| Versión | 2.3.0 |
| Tipo | funcionalidad |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

## Qué se pidió

Tres cosas, sobre la maqueta del equipo:

1. integrar la mascota (el equipo adjuntó las imágenes);
2. cambiar la navegación a la de la maqueta;
3. que el buscador muestre sugerencias mientras se escribe.

## Qué se hizo

### Navegación (ver [ADR-0011](../decisiones/ADR-0011-el-mapa-como-pantalla-principal.md))

- El **mapa es la pantalla principal**; antes lo era el chat.
- Se elimina el selector "Preguntar / Mapa". Al chat se entra con el botón
  "Pregúntame lo que necesites" y se vuelve con "← Volver al mapa".
- `estado.inicializar()` y `estado.salir()` abren en el mapa.

### Sugerencias al escribir

`panel_mapa.py` — el campo de destino pasa de `text_input` a `selectbox`.
Streamlit solo filtra opciones mientras se teclea en el segundo: es la lista
desplegable que muestra la maqueta (escribir "B0" y ver B01, B02, B03…).

**Sin perder lo que ya había**: con `accept_new_options=True` se puede escribir
cualquier cosa y, si no es una opción del catálogo, la resuelve la búsqueda
tolerante a erratas de siempre. Así "biblioteka" sigue funcionando.

### Mascota

- `ui/tema.py` — `mascota()`, `avatar_asistente()` y `css_mascota()`.
- La mascota es el **avatar del asistente** en el chat y va **dentro del botón**
  que abre la conversación.
- **Si el archivo no está, la aplicación funciona igual**: el avatar cae al
  emoji y el botón se ve sin imagen. Se comprobó con y sin el archivo.

## Por qué así

Dos cosas de la maqueta no se copiaron literal, y ADR-0011 explica por qué: el
botón de la mascota va arriba y no flotando sobre el plano (abajo queda fuera
de pantalla, se vio en el navegador), y lleva texto además de la imagen (un
botón sin texto no se puede etiquetar para lectores de pantalla desde
Streamlit).

## Cómo se probó

Con la aplicación levantada y el navegador:

- Buscador: escribir "B0" despliega B01–B09; elegir una fija el destino.
- Botón de la mascota abre el chat; "← Volver al mapa" vuelve.
- Ya no queda rastro del selector "Preguntar / Mapa".
- **Con y sin el archivo de la mascota**: sin él, el botón y el chat funcionan
  igual.
- Errores que solo se vieron mirando, no leyendo el código:
  - el botón salía **sin la imagen**: la regla `background: rojo !important` de
    los botones borra el `background-image`. Se cambió a `background-color`;
  - el botón quedaba **bajo el plano, fuera de pantalla**. Se subió;
  - el campo de destino seguía azul: el `selectbox` de esta versión usa
    `react-aria`, no `data-baseweb`, que fue lo primero que probé.
- `pytest` (menos `tests/test_proveedores.py`, roto en `main` de antes): 63 ok.
- `ruff check src tests scripts`: limpio.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | Cambia cómo se navega: quien conocía el selector ya no lo encuentra |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No |

## Al desplegar

**Copiar las dos imágenes de la mascota a `assets/`**, con estos nombres
exactos:

| Archivo | Qué es | Dónde se usa |
|---|---|---|
| `assets/mascota.png` | la cara | avatar del asistente y botón del chat |
| `assets/mascota_cuerpo.png` | cuerpo entero | todavía no se usa; queda para la pantalla de bienvenida |

Sin ellas la aplicación funciona, solo que sin mascota.

## Qué quedó pendiente

- **Las imágenes de la mascota no están en el repositorio**: el equipo las
  compartió en la conversación, pero hay que copiarlas a `assets/`.
- **Pantalla de bienvenida** (la del "¡BIENVENIDO!" con la mascota entera) y
  **pantalla de registro**: están en la maqueta y no se implementaron. El
  registro depende de que haya cuentas de verdad (ADR-0010).
- **La cabecera no tiene el menú ni el avatar de la maqueta**: hoy son la barra
  lateral de Streamlit y la sesión con clave compartida.
- **`tests/test_proveedores.py` sigue roto en `main`**, de antes de esta entrega.
